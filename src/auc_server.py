#Zhihao Wang zwang238

import socket
import threading
import sys
PORT = 12345
#default value "127.0.0.1"
SERVER_IP = "127.0.0.1"


class AuctioneerServer:
    def __init__(self, PORT):
        #socket and bind 
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((SERVER_IP, PORT))
        self.server.listen(5)
        self.bidding_in_progress = False
        self.seller_connected = None    #the variable will store the current seller to send the msg to 
        self.seller_setting = False     #the bool represents if the seller is setting request or not 
        self.type = 0                   #default values
        self.min_price = 100
        self.buyers = []
        self.item = "NAME"
        self.bids = 0
        print(f"Auctioneer is ready for hosting auctions!\n")


    def handle_bid(self, buyer, bidlist): #the function is used in multi process bid checking.
        while True:
            bid = buyer.recv(1024).decode()
            if not (bid.isdigit() and int(bid) >= 0):
                msg = "Server: Invalid bid. Please submit a positive integer!"
                buyer.send(msg.encode())
            else:
                bidlist[buyer] = int(bid)
                msg = "Server: Bid received. Please wait...."
                buyer.send(msg.encode())
                break

    def handle_client(self, client, addr): 
        #uf no current seller, next role will be seller. 
        if not self.seller_connected:
            role = "Seller"
        else:
            role = "Buyer"
        client.send(role.encode())  #send the role back to client.
        if role == "Seller":
            print(f"Seller is connected from {addr[0]}:{addr[1]}")
            self.seller_setting = True  #seller is doing configuration from now
            self.seller_connected = client  #store the current seller
            while True:
                item = client.recv(1024).decode() 
                parts = item.split(' ')
                if ((len(parts) != 4)):#if not 4 parts in all return false
                    error_msg = "Server: Incorrect format"
                    client.send(error_msg.encode())
                    continue

                if parts[0] not in ['1', '2']:#type is not 1 or 2
                    error_msg = "Server: Incorrect format"
                    client.send(error_msg.encode())
                    continue

                if not parts[1].isdigit() or int(parts[1]) <= 0:# if min price is not digits or positive value
                    error_msg = "Server: Incorrect format"
                    client.send(error_msg.encode())
                    continue

                if not parts[2].isdigit() or not (0 < int(parts[2]) < 10):# if min price is not digits or positive value and not from 0 to 10
                    error_msg = "Server: Incorrect format"
                    client.send(error_msg.encode())
                    continue

                if len(parts[3]) > 255:# if name is larger than 255
                    error_msg = "Server: Incorrect format"
                    client.send(error_msg.encode())
                    continue

                print(">> New Seller Thread spawned")#so create new seller thread
                msg = "Auction Request received. Now waiting for the Buyer."
                print(msg)
                print("")
                client.send(msg.encode())
                self.type = int(parts[0])
                self.min_price = int(parts[1])
                self.bids = int(parts[2])
                self.item = parts[3]
                self.seller_setting = False#seller stop configurating
                break
        elif role == "Buyer":
            if self.seller_setting:
                # if a seller is configurating, send the error message the close the connection
                msg = "Server is busy. Try to connect again later."
                client.send(msg.encode())
                client.close()
                return
            # record all buyer client in a buyer list
            if len(self.buyers) == self.bids:
                msg = "Server is busy. Try to connect again later."
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
                bidlist ={}         #make a dictionary of bid to store all the buyers with respective bid value
                print("Requested number of bidders arrived. Let's start bidding!\n")
                print(">> New Bidding Thread spawned")
                self.bidding_in_progress = True
                threads = []

                start_msg = "Server: Auction is starting. Place your bids!"
                for buyer in self.buyers:#multi processing on each thread
                    buyer.send(start_msg.encode())
                    thread = threading.Thread(target=self.handle_bid, args=(buyer, bidlist))
                    thread.start()
                    threads.append(thread)

                for thread in threads:
                    thread.join()

                for index, bid in enumerate(bidlist.values()):
                    print(f">> Buyer {index + 1} bid ${bid}")
                highest_bid = max(bidlist, key=bidlist.get)                     #this is the largest value of bid
                sorted_bids = sorted(bidlist.values(), reverse=True)    
                second_highest_bid = sorted_bids[1] if len(sorted_bids) > 1 else None   #this is the second largest value of bid using in second-price
                if self.type == 1:
                    second_highest_bid =bidlist[highest_bid]       

                #this is the part of code for 1-price and 2-price             
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
                    #when largest price is less than min price, the item will not be sold.
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
        print("Usage: python auc_server.py <#port>")
        sys.exit(1)
    PORT = int(sys.argv[1])
    server = AuctioneerServer(PORT)
    server.start()