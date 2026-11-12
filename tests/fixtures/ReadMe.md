Format of dictionaries containing arguments and expected results:  
```
{
    "test_name": {
        "type": "assert_equal",
        "args":{
            "gene": "FUNDC1",
            "sequence": ""
        },
        "expected_result": []
    },
    
    "test_name": {
        "type": "assert_none",
        "args":{
            "gene": "",
        },
        "expected_result": None
    },
    
    "test_name": {
        "type": "error",
        "args":{
            "gene": "banana",
        },
        "expected_result": "ValueError"
    },
}
```

Note: Results returned in a DataFrame format need to be converted to a list and NA values should be dropped (df.dropna(axis=1).values.tolist()).  

**Test types:**  
See: https://github.com/scverse/gget/blob/c7044545494ef72c042db1a5c5f116f45fbf28a3/tests/from_json.py#L197C1-L197C7
