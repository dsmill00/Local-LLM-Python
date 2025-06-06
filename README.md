Building Llama Local LLM using 7b-instruct-v0.1.Q5_K_M.gguf

Folder PATH listing for volume D. 

D:.
|   chat_memory.json
|   last_prompt_debug.txt
|   main.py
|   vector.index
|   vector_meta.pkl
|
+---backend
|   |   config.py
|   |   file_extractor.py
|   |   llama_runner.py
|   |   memory.py
|   |   output_cleaner.py
|   |   plugin_manager.py
|   |   prompt_optimizer.py
|   |   tokenizer.py
|   |   vector_store.py
|   |   __init__.py
|   |
|   +---plugins
|   |   |   plugin_interface.py
|   |   |   __init__.py
|   |   |
|   |   \---__pycache__
|   |           plugin_datetime.cpython-313.pyc
|   |           plugin_interface.cpython-313.pyc
|   |           __init__.cpython-313.pyc
|   |
|   \---__pycache__
|           config.cpython-313.pyc
|           file_extractor.cpython-313.pyc
|           llama_runner.cpython-313.pyc
|           llm_runner.cpython-313.pyc
|           memory.cpython-313.pyc
|           output_cleaner.cpython-313.pyc
|           plugin_manager.cpython-313.pyc
|           prompt_optimizer.cpython-313.pyc
|           tokenizer.cpython-313.pyc
|           vector_store.cpython-313.pyc
|           __init__.cpython-313.pyc
|
+---logs
|       raw_llama_output.txt
|
\---ui
    |   main_window.py
    |   python_highlighter.py
    |   __init__.py
    |
    \---__pycache__
            main_window.cpython-313.pyc
            python_highlighter.cpython-313.pyc
            __init__.cpython-313.pyc
