from .utils import set_up_logger

logger = set_up_logger()


def gpt(
    prompt,
    api_key,
    model="gpt-3.5-turbo",
    temperature=1,
    top_p=1,
    stop=None,
    max_tokens=200,
    presence_penalty=0,
    frequency_penalty=0,
    logit_bias=None,
    out=None,
    verbose=True,
):
    """Generates natural language text based on a given prompt using the OpenAI API's 'openai.ChatCompletion.create' endpoint.

    Parameters
    ----------
    - prompt (str):             The input prompt to generate text from.
    - api_key (str):            Your OpenAI API key (see: https://platform.openai.com/account/api-keys).
    - model (str):              The name of the GPT model to use for generating the text. Default is "gpt-3.5-turbo".
                                See https://platform.openai.com/docs/models/gpt-4 for more information on the available models.
    - temperature (float)       Value between 0 and 2 that controls the level of randomness and creativity in the generated text.
                                Higher values result in more creative and varied text. Default is 1.
    - top_p (float)             Controls the diversity of the generated text as an alternative to sampling with temperature.
                                Higher values result in more diverse and unexpected text. Default is 1.
                                Note: OpenAI recommends altering this or temperature but not both.
    - stop (str)                A sequence of tokens to mark the end of the generated text. Default is None.
    - max_tokens (int)          Controls the maximum length of the generated text, in tokens. Default is 200.
    - presence_penalty (float)  Number between -2.0 and 2.0. Higher values result increase the model's likelihood to talk about new topics.
                                Default is 0.
    - frequency_penalty (float) Number between -2.0 and 2.0. Higher values decrease the model's likelihood to repeat the same line verbatim.
                                Default is 0.
    - logit_bias (dict)         A dictionary that specifies a bias towards certain tokens in the generated text. Default is None.
    - out (str)                 If provided, saves the generated text to a file with the specified path. Default is None.
    - verbose                   True/False whether to print progress information. Default True.

    Returns
    -------
    - A string containing the generated text.

    NOTE: OpenAI API calls are only 'free' for the first three months after generating your OpenAI Account
    (OpenAI provides a $5 credit that expires).
    You can define a hard billing limit (e.g. $1) here: https://platform.openai.com/account/billing/limits
    See their pricing and FAQ here: https://openai.com/pricing

    This module, including its source code, documentation and unittests, were partly written by OpenAI's Chat-GTP3.

    """
    # Check if cellxgene_census is installed
    try:
        import openai
    except ImportError:
        logger.error(
            """
            Some third-party dependencies are missing. Please run the following command:
            >>> gget.setup('gpt') or $ gget setup gpt

            Alternative: Install the openai package using pip (https://pypi.org/project/openai).
            """
        )
        return

    openai.api_key = api_key

    messages = [
        {"role": "user", "content": prompt},
    ]

    # https://platform.openai.com/docs/api-reference/chat/create
    if logit_bias is None:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            n=1,
            stream=False,
            stop=stop,
            max_tokens=max_tokens,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
        )
    else:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            n=1,
            stream=False,
            stop=stop,
            max_tokens=max_tokens,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            logit_bias=logit_bias,
        )

    if verbose:
        logger.info(f"Total tokens used for API call to model '{model}': {response['usage']['total_tokens']}")

    texts = response["choices"][0]["message"]["content"]

    if out:
        with open(out, "w") as f:
            f.write(texts)

    return texts + "\n"
