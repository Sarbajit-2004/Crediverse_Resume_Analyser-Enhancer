import tomllib, pathlib
print(tomllib.loads(pathlib.Path(".streamlit/secrets.toml").read_text(encoding="utf-8")))
