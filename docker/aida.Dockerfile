FROM ollama/ollama:latest

ENV OLLAMA_ORIGINS=http://0.0.0.0:11434

COPY Modelfile .

VOLUME ["/root/.ollama"]

RUN nohup bash -c "ollama serve &" && sleep 2 && ollama create aida -f Modelfile
