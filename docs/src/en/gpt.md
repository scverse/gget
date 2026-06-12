[<kbd> View page source on GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/en/gpt.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget gpt 💬
Generates natural language text based on a given prompt using the [OpenAI](https://openai.com/) API's 'openai.ChatCompletion.create' endpoint.
This module, including its source code, documentation and unit tests, were partly written by OpenAI's Chat-GTP3.  

NOTE:  
OpenAI API calls are only 'free' for the first three months after generating your OpenAI Account (OpenAI provides a $5 credit that expires).  
You can define a hard monthly billing limit (e.g. $1) [here](https://platform.openai.com/account/billing/limits).  
See their pricing and FAQ [here](https://openai.com/pricing).  
Get your OpenAI API key [here](https://platform.openai.com/account/api-keys).  

Returns: A string containing the generated text.  

Before using `gget gpt` for the first time, run `gget setup gpt` / `gget.setup("gpt")` once (also see [`gget setup`](setup.md)).  

**Positional argument**  
`prompt`  
The input prompt to generate text from (str).  

`api_key`  
Your OpenAI API key (str) ([get your API key](https://platform.openai.com/account/api-keys)).  

**Optional arguments**  
`-m` `--model`  
The name of the GPT model to use for generating the text (str). Default is "gpt-3.5-turbo".  
See https://platform.openai.com/docs/models/gpt-4 for more information on the available models.  

`-temp` `--temperature`  
Value between 0 and 2 that controls the level of randomness and creativity in the generated text (float).  
Higher values result in more creative and varied text. Default is 1.  

`-tp` `--top_p`  
Controls the diversity of the generated text as an alternative to sampling with temperature (float).  
Higher values result in more diverse and unexpected text. Default is 1.  
Note: OpenAI recommends altering this or temperature but not both.  

`-s` `--stop`  
A sequence of tokens to mark the end of the generated text (str). Default is None.  

`-mt` `--max_tokens`  
Controls the maximum length of the generated text, in tokens (int). Default is 200.  

`-pp` `--presence_penalty`  
Number between -2.0 and 2.0. Higher values result increase the model's likelihood to talk about new topics (float). Default is 0.  

`-fp` `--frequency_penalty`  
Number between -2.0 and 2.0. Higher values decrease the model's likelihood to repeat the same line verbatim (float). Default is 0.  

`-lb` `--logit_bias`  
A dictionary that specifies a bias towards certain tokens in the generated text (dict). Default is None.  

`-o` `--out`  
If provided, saves the generated text to a file with the specified path (str). Default: Standard out.  


### Example
```bash
gget gpt "How are you today GPT?" your_api_token
```
```python
# Python
print(gget.gpt("How are you today GPT?", "your_api_token"))
```

<br>

<img width="725" alt="Screen Shot 2023-03-18 at 3 42 32 PM" src="https://user-images.githubusercontent.com/56094636/226143902-6fa2d0c7-7eea-4382-b1d2-df6c3f0d5fd5.png">
