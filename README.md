# MD-DB
Network Key-Value DB implementation

## How To:

Required python3.10+

* Compile the .proto file:
```cmd
\D-DB\external\protoc-3.19.4-win64> bin\protoc.exe -I=..\..\ --python_out=..\..\ ..\..\mdlib\md.proto
```

* Install the packages:
```cmd
pip install -r requirements.txt
```

* Run the main.py files (outside the MD-DB folder):
```cmd
md_server
md_client
```
