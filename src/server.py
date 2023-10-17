import socket
import threading
import sys
PORT = 12345
SERVER_IP = "127.0.0.1"


class AuctioneerServer:
    def __init__(self, PORT):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((SERVER_IP, PORT))
        self.server.listen(5)
        self.bidding_in_progress = False
        self.seller_connected = None
        self.seller_setting = False
        self.type = 0
        self.min_price = 100
        self.buyers = []
        self.item = "NAME"
        self.bids = 0
        print(f"Auctioneer is ready for hosting auctions!\n")


    def handle_bid(self, buyer, bidlist):
        while True:
            bid = buyer.recv(1024).decode()
            if not (bid.isdigit() and int(bid) >= 0):
                msg = "Server: Invalid bid. Please submit a positive integer!"
                buyer.send(msg.encode())
            else:
                bidlist[buyer] = bid
                msg = "Server: Bid received. Please wait...."
                buyer.send(msg.encode())
                break

    def handle_client(self, client, addr):
        if not self.seller_connected:
            role = "Seller"
        else:
            role = "Buyer"
        client.send(role.encode())
        if role == "Seller":
            # if some seller has been connecting, send the error msg
            print(f"Seller is connected from {addr[0]}:{addr[1]}")
            self.seller_setting = True
            self.seller_connected = client
            while True:
                # Handle seller logic here
                item = client.recv(1024).decode()  # For example
                parts = item.split(' ')
                if ((len(parts) != 4)):
                    error_msg = "Server: Incorrect format"
                    client.send(error_msg.encode())
                    continue

                if parts[0] not in ['1', '2']:
                    error_msg = "Server: Incorrect format"
                    client.send(error_msg.encode())
                    continue

                if not parts[1].isdigit() or int(parts[1]) <= 0:
                    error_msg = "Server: Incorrect format"
                    client.send(error_msg.encode())
                    continue

                if not parts[2].isdigit() or not (0 < int(parts[2]) < 10):
                    error_msg = "Server: Incorrect format"
                    client.send(error_msg.encode())
                    continue

                if len(parts[3]) > 255:
                    error_msg = "Server: Incorrect format"
                    client.send(error_msg.encode())
                    continue

                print(">> New Seller Thread spawned")
                msg = "Auction Request received. Now waiting for the Buyer."
                print(msg)
                print("")
                client.send(msg.encode())
                self.type = int(parts[0])
                self.min_price = int(parts[1])
                self.bids = int(parts[2])
                self.item = parts[3]
                self.seller_setting = False
                break
        elif role == "Buyer":
            if self.seller_setting:
                # 如果另一个卖家正在输入，拒绝此卖家的连接
                msg = "Server is busy2. Try to connect again later."
                client.send(msg.encode())
                client.close()
                return
            # record all buyer client in a buyer list
            if len(self.buyers) == self.bids:
                msg = "Server is busy1. Try to connect again later."
                client.send(msg.encode())
                client.close()
                return
            self.buyers.append(client)
            print(f"Buyer {len(self.buyers)} is connected from {addr[0]}:{addr[1]}")
            # wait until #bids numbers are satisfied
            if len(self.buyers) < self.bids:
                error_msg = "waiting"
                client.send(error_msg.encode())
            else:
                bidlist ={}
                print("Requested number of bidders arrived. Let's start bidding!\n")
                print(">> New Bidding Thread spawned")
                self.bidding_in_progress = True
                threads = []

                start_msg = "Server: Auction is starting. Place your bids!"
                for buyer in self.buyers:
                    buyer.send(start_msg.encode())
                    thread = threading.Thread(target=self.handle_bid, args=(buyer, bidlist))
                    thread.start()
                    threads.append(thread)

                # 等待所有的投标线程完成
                for thread in threads:
                    thread.join()

                for index, bid in enumerate(bidlist.values()):
                    print(f">> Buyer {index + 1} bid ${bid}")
                highest_bid = max(bidlist, key=bidlist.get)
                sorted_bids = sorted(bidlist.values(), reverse=True)
                second_highest_bid = sorted_bids[1] if len(sorted_bids) > 1 else None
                if self.type == 1:
                    second_highest_bid =bidlist[highest_bid]
                if int(second_highest_bid) >= self.min_price:
                    for buyer, bid in bidlist.items():
                            msg = ""
                            if buyer == highest_bid:
                                msg = f"You won this item {self.item}! Your payment due is ${second_highest_bid}."
                            else:
                                msg = f"Unfortunately you did not win in the last round."
                            buyer.send(msg.encode())
                    new_msg = f"Success! Your item {self.item} has been sold for ${second_highest_bid}"
                    self.seller_connected.send(new_msg.encode())
                    print(f">> Item sold! The highest bid is ${bidlist[highest_bid]}. The actual payment is ${second_highest_bid}")
                    self.bidding_in_progress = False
                    self.seller_connected = None
                else:
                    for buyer, bid in bidlist.items():
                            msg = f"Unfortunately you did not win in the last round."
                            buyer.send(msg.encode())
                    new_msg = f"Unfortunately your item {self.item} hasn't been sold"
                    self.seller_connected.send(new_msg.encode())
                    print(f">> No! Item not sold!")
                    self.bidding_in_progress = False
                    self.seller_connected = None
                self.buyers = []
                
                    

    def start(self):
        while True:
            conn, addr = self.server.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python server.py <#port>")
        sys.exit(1)
    PORT = int(sys.argv[1])
    server = AuctioneerServer(PORT)
    server.start()