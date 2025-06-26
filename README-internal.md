## install required packages

pip install -r requirements.txt


## Import

### local

Change parameters "port" and "password" in import2mysql.py to match your setup and run import2mysql.py

### production

- connect via VPN/internet
- connect to production server and port forward to local port 3007 via
   ```ssh -L 3307:localhost:3306 dh-parz@130.92.252.118```
- Change parameters "port" and "password" in mysql_Import.py to match your setup and run main,py or mysql_Import.py