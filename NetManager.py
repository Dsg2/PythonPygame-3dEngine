class NetManager():
    def __init__(self, mode, shared = []):
        self.data = {"clients": {}, "syncqueue": []}
        self.sharedkeys = shared
        if isinstance(mode, tuple):
            self.cid = [-1]*mode[1]
            self.mode = "server"
        else:
            self.mode = "client"
    
    #server does load(connectedids)
    def load(self, clientid=None):
        if self.mode == "server":
            p = 0
            for val in self.cid:
                if val != -1:
                    p = p + 1
            notinc = []
            if p < len(clientid):
                for val in clientid:
                    if val not in self.cid:
                        notinc.append(val)
            freeslots = []
            for ind, val in enumerate(self.cid):
                if val == -1:
                    freeslots.append(ind)
            for ind, val in enumerate(freeslots):
                if ind < len(notinc):
                    self.cid[val] = notinc[ind]
            return(self.cid)
        else:
            return(self.data)
    
    #pass txt and client_id
    def recv(self, inp, cid=-1):
        inp = inp.split(maxsplit=2)
        if len(inp) > 1 and isinstance(inp, list):
            sid = inp[0]
            if sid.isnumeric():
                sid = int(sid)
            key = inp[1]
            rdata = inp[2]
            if sid == "own":
                if key == "sid":
                    self.data["syncqueue"].append(("setsid", int(rdata)))
                else:
                    if "&" in rdata:
                        rdata = rdata.split("&")
                    self.data["syncqueue"].append((key, rdata))
            else:
                if "&" in rdata:
                    data = rdata.split("&")
                else:
                    data = rdata
                if sid not in self.data["clients"]:
                    self.data["clients"][sid] = {}
                self.data["clients"][sid][key] = data
                if self.mode == "server":
                    if key in self.sharedkeys:
                        if int(sid) != -1:
                            self.data["syncqueue"].append((None, f"{sid} {key} {rdata}", self.cid[int(sid)]))
        else:
            if inp[0] == "reqsid":
                try:
                    self.data["syncqueue"].append((cid, f"own sid {self.cid.index(cid)}", None))
                except Exception as e:
                    print(e)
        return(self.data)
    
    def send(self, sid, key, data, targ=None, excl=None):
        if isinstance(data, tuple) or isinstance(data, list):
            data = map(str, data)
            data = "&".join(data)
        if self.mode == "client":
            #print("{sid} {key} {data}")
            return(f"{sid} {key} {data}")
        elif self.mode == "server":
            return((targ, f"{sid} {key} {data}", excl))
    
    def sync(self, inp):
        self.data = inp