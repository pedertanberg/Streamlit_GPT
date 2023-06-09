import random
import os
from urllib.parse import urlencode

import streamlit as st
import streamlit.components.v1 as components
import torch
from transformers import pipeline, set_seed
from transformers import AutoTokenizer, AutoModelForCausalLM


HF_AUTH_TOKEN = "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"
DEVICE = os.environ.get("cuda:0", "cpu")  # cuda:0
DTYPE = torch.float32 if DEVICE == "cpu" else torch.float16
MODEL_NAME = os.environ.get("MODEL_NAME", "NbAiLab/nb-gpt-j-6B-alpaca")
MAX_LENGTH = int(os.environ.get("MAX_LENGTH", 256))
print("hello Boys")
HEADER_INFO = """
# CBS_Alpaca-GPT-j
Norwegian GPT-J-6B NorPaca Model.
""".strip()
LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Logo_CopenhagenBusinessSchool.svg/1200px-Logo_CopenhagenBusinessSchool.svg.png"
SIDEBAR_INFO = f"""
<div align=center>
<img src="{LOGO}" width=100/>

# NB-GPT-J-6B-NorPaca

</div>

NB-GPT-J-6B NorPaca is a hybrid of a GPT-3 and Llama model, trained on the Norwegian Colossal Corpus and other Internet sources. It is a 6.7 billion parameter model, and is the largest model in the GPT-J family.

This model has been trained with [Mesh Transformer JAX](https://github.com/kingoflolz/mesh-transformer-jax) using TPUs provided by Google through the Tensor Research Cloud program, starting off the [GPT-J-6B model weigths from EleutherAI](https://huggingface.co/EleutherAI/gpt-j-6B), and trained on the [Norwegian Colossal Corpus](https://huggingface.co/datasets/NbAiLab/NCC) and other Internet sources. *This demo runs on {DEVICE.split(':')[0].upper()}*.

For more information, visit the [model repository](https://huggingface.co/CBSMasterThesis).

## Configuration
""".strip()
PROMPT_BOX = "Enter your text..."
EXAMPLES = [
    "Nedenfor er en instruksjon som beskriver en oppgave. Skriv et svar som fullfører forespørselen på riktig måte. ### Instruksjon: Analyser fordelene ved å jobbe i et team. ### Respons:",
    'Nedenfor er en instruksjon som beskriver en oppgave. Skriv et svar som fullfører forespørselen på riktig måte. ### Instruksjon: Oppsummer den faglige artikkelen "Kunstig intelligens og arbeidets fremtid". ### Respons:',
    'Nedenfor er en instruksjon som beskriver en oppgave. Skriv et svar som fullfører forespørselen på riktig måte. ### Instruksjon: Generer et kreativt slagord for en bedrift som bruker fornybare energikilder. ### Respons:',
    'Nedenfor er en instruksjon som beskriver en oppgave. Skriv et svar som fullfører forespørselen på riktig måte. ### Instruksjon: Regn ut arealet av en firkant med lengde 10m. Skriv ut et flyttall. ### Respons:',
]


def style():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300&display=swap%22%20rel=%22stylesheet%22" rel="stylesheet">
    <style>
    .ltr,
    textarea {
        font-family: Roboto !important;
        text-align: left;
        direction: ltr !important;
    }
    .ltr-box {
        border-bottom: 1px solid #ddd;
        padding-bottom: 20px;
    }
    .rtl {
        text-align: left;
        direction: ltr !important;
    }
    span.result-text {
        padding: 3px 3px;
        line-height: 32px;
    }
    span.generated-text {
        background-color: rgb(118 200 147 / 13%);
    }
    </style>""", unsafe_allow_html=True)


class Normalizer:
    def remove_repetitions(self, text):
        """Remove repetitions"""
        first_ocurrences = []
        for sentence in text.split("."):
            if sentence not in first_ocurrences:
                first_ocurrences.append(sentence)
        return '.'.join(first_ocurrences)

    def trim_last_sentence(self, text):
        """Trim last sentence if incomplete"""
        return text[:text.rfind(".") + 1]

    def clean_txt(self, text):
        return self.trim_last_sentence(self.remove_repetitions(text))


class TextGeneration:
    def __init__(self):
        self.tokenizer = None
        self.generator = None
        self.task = "text-generation"
        self.model_name_or_path = MODEL_NAME
        set_seed(42)

    def load(self):
        print("Loading model... ", end="")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name_or_path, use_auth_token=HF_AUTH_TOKEN if HF_AUTH_TOKEN else None,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name_or_path, use_auth_token=HF_AUTH_TOKEN if HF_AUTH_TOKEN else None,
            pad_token_id=self.tokenizer.eos_token_id, eos_token_id=self.tokenizer.eos_token_id,
            torch_dtype=DTYPE, low_cpu_mem_usage=False if DEVICE == "cpu" else True
        ).to(device=DEVICE, non_blocking=True)
        _ = self.model.eval()
        device_number = -1 if DEVICE == "cpu" else int(DEVICE.split(":")[-1])
        self.generator = pipeline(
            self.task, model=self.model, tokenizer=self.tokenizer, device=device_number)
        print("Done")
        # with torch.no_grad():
        # tokens = tokenizer.encode(prompt, return_tensors='pt').to(device=device, non_blocking=True)
        # gen_tokens = self.model.generate(tokens, do_sample=True, temperature=0.8, max_length=128)
        # generated = tokenizer.batch_decode(gen_tokens)[0]

        # return generated

    def generate(self, prompt, generation_kwargs):
        max_length = len(self.tokenizer(prompt)[
                         "input_ids"]) + generation_kwargs["max_length"]
        generation_kwargs["max_length"] = min(
            max_length, self.model.config.n_positions)
        # generation_kwargs["num_return_sequences"] = 1
        # generation_kwargs["return_full_text"] = False
        return self.generator(
            prompt,
            **generation_kwargs,
        )[0]["generated_text"]


# @st.cache(allow_output_mutation=True, hash_funcs={AutoModelForCausalLM: lambda _: None})
@st.cache(allow_output_mutation=True, hash_funcs={TextGeneration: lambda _: None})
def load_text_generator():
    generator = TextGeneration()
    generator.load()
    return generator


def main():
    st.set_page_config(
        page_title="NB-GPT-J-6B-NorPaca",
        page_icon="🇳🇴",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    style()
    with st.spinner('Loading the model. Please, wait...'):
        generator = load_text_generator()

    st.sidebar.markdown(SIDEBAR_INFO, unsafe_allow_html=True)
    query_params = st.experimental_get_query_params()
    if query_params:
        st.experimental_set_query_params(**dict())

    max_length = st.sidebar.slider(
        label='Max words to generate',
        help="The maximum length of the sequence to be generated.",
        min_value=1,
        max_value=MAX_LENGTH,
        value=int(query_params.get("max_length", [50])[0]),
        step=1
    )
    top_k = st.sidebar.slider(
        label='Top-k',
        help="The number of highest probability vocabulary tokens to keep for top-k-filtering",
        min_value=40,
        max_value=80,
        value=int(query_params.get("top_k", [50])[0]),
        step=1
    )
    top_p = st.sidebar.slider(
        label='Top-p',
        help="Only the most probable tokens with probabilities that add up to `top_p` or higher are kept for "
             "generation.",
        min_value=0.0,
        max_value=1.0,
        value=float(query_params.get("top_p", [0.95])[0]),
        step=0.01
    )
    temperature = st.sidebar.slider(
        label='Temperature',
        help="The value used to module the next token probabilities",
        min_value=0.1,
        max_value=10.0,
        value=float(query_params.get("temperature", [0.8])[0]),
        step=0.05
    )
    do_sample = st.sidebar.selectbox(
        label='Sampling?',
        options=(False, True),
        help="Whether or not to use sampling; use greedy decoding otherwise.",
        index=int(query_params.get("do_sample", ["true"])[
                  0].lower()[0] in ("t", "y", "1")),
    )
    do_clean = st.sidebar.selectbox(
        label='Clean text?',
        options=(False, True),
        help="Whether or not to remove repeated words and trim unfinished last sentences.",
        index=int(query_params.get("do_clean", ["true"])[
                  0].lower()[0] in ("t", "y", "1")),
    )
    generation_kwargs = {
        "max_length": max_length,
        "top_k": top_k,
        "top_p": top_p,
        "temperature": temperature,
        "do_sample": do_sample,
        "do_clean": do_clean,
    }
    st.markdown(HEADER_INFO)
    prompts = EXAMPLES + ["Custom"]
    prompt = st.selectbox('Examples', prompts, index=len(prompts) - 1)

    if prompt == "Custom":
        prompt_box = query_params.get("text", [PROMPT_BOX])[0].strip()
    else:
        prompt_box = prompt

    text = st.text_area("Enter text", prompt_box)
    generation_kwargs_ph = st.empty()
    cleaner = Normalizer()
    if st.button("Generate!") or text != PROMPT_BOX:
        output = st.empty()
        with st.spinner(text="Generating..."):
            generation_kwargs_ph.markdown(
                ", ".join([f"`{k}`: {v}" for k, v in generation_kwargs.items()]))
            if text:
                share_args = {"text": text, **generation_kwargs}
                st.experimental_set_query_params(**share_args)
                for _ in range(5):
                    generated_text = generator.generate(
                        text, generation_kwargs)
                    if do_clean:
                        generated_text = cleaner.clean_txt(generated_text)
                    if generated_text.strip().startswith(text):
                        generated_text = generated_text.replace(
                            text, "", 1).strip()
                    output.markdown(
                        f'<p class="ltr ltr-box">'
                        f'<span class="result-text">{text} <span>'
                        f'<span class="result-text generated-text">{generated_text}</span>'
                        f'</p>',
                        unsafe_allow_html=True
                    )
                    if generated_text.strip():
                        components.html(
                            f"""
                                <a class="twitter-share-button"
                                data-text="Check my prompt using NB-GPT-J-6B-NorPaca!🇳🇴 https://ai.nb.no/demo/nb-gpt-j-6B-NorPaca/?{urlencode(share_args)}"
                                data-show-count="false">
                                data-size="Small"
                                data-hashtags="nb,gpt-j"
                                Tweet
                                </a>
                                <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
                            """
                        )
                        break
                if not generated_text.strip():
                    st.markdown(
                        "*Tried 5 times but did not produce any result. Try again!*")


if __name__ == '__main__':
    main()
