# MD-DB
Network Key-Value DB implementation

## How To:

Required python3.10+

* Compile the .proto file:
```cmd
<PROJECT_DIRECTORY>\external\protoc-3.19.4-win64> bin\protoc.exe -I=..\..\ --python_out=..\..\ ..\..\mdlib\mdlib\md.proto
```

* Install the packages:
```cmd
pip install -r requirements.txt
```

* Run the main.py files:
When running for the first time, you need to add an admin user.
Only admin users can add permissions to users:

```cmd
md_server -h 127.0.0.1 -p 8888 --add-admin-user --admin-client-id <admin-id> --admin-password <admin-password>
```

And then run the client:
```cmd
md_client -h 127.0.0.1 -p 8888 -d users --client-id <admin-id>
```

You also can create new user:
```cmd
md_client -h 127.0.0.1 -p 8888 -d mydb --client-id <client-id> --add-user
```

* Run the tests:
```cmd
cd <PROJECT_DIRECTORY>\md_tests
pytest .
```
