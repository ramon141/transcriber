# Regras do Projeto

- Coloque qualquer arquivo de documentação na pasta `./documentation`
- Coloque qualquer arquivo de script na pasta `./scripts`
- Coloque qualquer migration na pasta `./migrations` nomeada como `NNN_descricao.sql`
- Evite o uso de literais — utilize constantes ou enums
- Sempre faça a tipagem correta com type hints Python; use pyright para validar (`typeCheckingMode: "basic"`, 0 erros); nunca use `any` ou `unknown`
- Jamais crie um arquivo com mais de 300 linhas; refatore
- Jamais crie uma função com mais de 40 linhas; refatore
- O app Streamlit roda na porta 8501 (`streamlit run streamlit_app.py`)
- Toda alteração de schema vai em `./migrations` — nunca DDL avulso; migrations devem ser idempotentes
- Estado de sessão inicializado exclusivamente em `ui/state.py → init_state()`; `st.set_page_config` apenas em `streamlit_app.py`
- Integrações externas (Supabase, Notion, Pyannote) nunca devem quebrar o fluxo principal; trate exceções e mostre mensagem clara ao usuário via `st.error()` / `st.warning()`
- Opte sempre por criar uma linha em branco quando achar necessário para facilitar a leitura
- Não use código completo em uma única linha quando prejudicar a legibilidade; evite:

```python
# Ruim
return {"sucesso": True, "dados": [] if diarizar else resultados, "total": len(resultados)}

# Bom
return {
    "sucesso": True,
    "dados": [] if diarizar else resultados,
    "total": len(resultados),
}
```
