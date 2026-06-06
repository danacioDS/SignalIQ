### Oracle data
## include this file in ignoe
ssh ubuntu@163.176.128.135

#####
# Terminal 1
ssh ubuntu@163.176.128.135
cd ~/SignalIQ
python3 api.py

# Terminal 2 (nueva ventana)
ssh -L 8000:localhost:8000 ubuntu@163.176.128.135

# Terminal 3 (nueva ventana)
cd ~/repo_lab/SignalIQ
python3 -m http.server 8080

# Navegador: http://localhost:8080/dashboard.html

###
# Terminal 1 - API
ssh ubuntu@163.176.128.135
cd ~/SignalIQ
python3 api.py

# Terminal 2 - Túnel
ssh -L 8000:localhost:8000 ubuntu@163.176.128.135

# Terminal 3 - Dashboard
cd ~/repo_lab/SignalIQ
python3 -m http.server 8080

# Navegador
http://localhost:8080/dashboard.html