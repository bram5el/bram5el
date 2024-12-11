# OpenVPN status script
  _Scrip based on [Simple OpenVPN Server Statistics](https://sigterm.sh/2009/07/16/simple-openvpn-server-statistics/)_
  The script downloads openvpn status data and saves it in json format. It stores data about connected clients and accumulates it. It is possible to display current status data openvpn, stored openvpn data. Additionally, it is possible to run a periodic state update at a specified interval to use the script as a service.

Before running, ensure your server is actually saving the stats somewhere (/etc/openvpn/openvpn.status in my example):
```bash
greg@leonis:~$ grep status /etc/openvpn/server.conf
status openvpn.status
```
Here is script ouput example:
```bash
Common Name               Virtual Address    Real Address             Sent        Received           Connected Since                  Last Ref
-------------------------------------------------------------------------------------------------------------------------------------------------
laptop-office             10.8.0.5           93.115.98.157         1.89 GB        42.43 MB                            Mon Dec  9 15:05:00 2024
mobile-work               10.8.0.7           93.115.98.157       175.68 MB         7.65 MB                            Tue Dec 10 13:46:38 2024
mobile-private            10.8.0.2           42.151.28.110         5.44 MB         1.82 MB                            Mon Dec  9 15:58:24 2024
pc                        10.8.0.6           46.102.77.123        43.77 KB        35.58 KB  Wed Dec 11 09:26:30 2024  Wed Dec 11 09:29:17 2024
```