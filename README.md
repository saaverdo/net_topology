# net_topology
---

### Steps to run

Install required packages:  

```
sudo apt install -y python3-pip python3-venv
```

Clone theis repo:  

```
git clone https://github.com/saaverdo/net_topology.git -b cisco
```

Create python virtual environment (optional, but recommended):  

```
python3 -m venv venv
source venv/bin/activate
```

Install required python molules:  

```
pip install -r requirements.txt
```

Run script:  

```
python main.py -i inventory.yml -p 15 -proto lldp
```
