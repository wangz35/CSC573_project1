import socket
import sys

PORT = 12345
SERVER_IP = "127.0.0.1"

class AuctionClient:
    def __init__(self, SERVER_IP, PORT):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((SERVER_IP, PORT))
        self.role = None

    def start(self):
        self.role = self.client.recv(1024).decode()
        print(f"Connected to the Auctioneer server.\n")
        if self.role == "Seller":
            print(f"Your role is : [{self.role}]")
            while True:
                item = input("Please submit auction request: ")
                self.client.send(item.encode())
                response = self.client.recv(1024).decode()
                if response == "Server: Incorrect format":
                    print(response)
                    continue
                if response == "Auction Request received. Now waiting for the Buyer.":
                    print("Server: Auction Start.")
                    break
            response = self.client.recv(1024).decode()
            print("")
            print("Auction finished!")
            print(response)
            print("Disconnecting from the Auctioneer server. Auction is over!")
            self.client.close()

        elif self.role == "Buyer":
            response = self.client.recv(1024).decode()
            if "busy" in response:
                print(response)
                return
            print(f"Your role is : [{self.role}]")
            if "waiting" in response:
                print("The Auctioneer is stilling waiting for other Buyers to connect...")
                response = self.client.recv(1024).decode()
            if "starting" in response:
                print("The bidding has started!")
                while True:
                    bid = input("Please submit your bid: \n")
                    self.client.send(bid.encode())
                    response = self.client.recv(1024).decode()
                    if "Invalid" in response:
                        print(response)
                    else:
                        print(response)
                        break
                response = self.client.recv(1024).decode()
                print("")
                print("Auction finished!")
                print(response)
                print("Disconnecting from the Auctioneer server. Auction is over!")
                self.client.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py <#ip> <#port>")
        sys.exit(1)
    SERVER_IP = sys.argv[1]
    PORT = int(sys.argv[2])
    client = AuctionClient(SERVER_IP, PORT)
    client.start()