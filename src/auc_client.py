#Zhihao Wang zwang238
import socket
import sys

PORT = 12345
SERVER_IP = "127.0.0.1"

class AuctionClient:
    def __init__(self, SERVER_IP, PORT):
        #socket of client
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((SERVER_IP, PORT))
        self.role = None            #the parameter stores the value of role

    def start(self):
        self.role = self.client.recv(1024).decode() #receive the role value
        print(f"Connected to the Auctioneer server.\n")
        if self.role == "Seller":
            print(f"Your role is : [{self.role}]")
            #have a while loop on repeating the auction request.
            while True:
                item = input("Please submit auction request: ")
                self.client.send(item.encode())
                response = self.client.recv(1024).decode()
                if response == "Server: Incorrect format":
                    print(response)#continue the while loop
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
            #if the response is including busy, print the whole response.
            if "busy" in response:
                print(response)
                return
            print(f"Your role is : [{self.role}]")
            # print all the response
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
        print("Usage: python auc_client.py <#ip> <#port>")
        sys.exit(1)
    SERVER_IP = sys.argv[1]
    PORT = int(sys.argv[2])
    client = AuctionClient(SERVER_IP, PORT)
    client.start()