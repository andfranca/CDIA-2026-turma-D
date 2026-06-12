import streamlit as st
import pandas as pd
import ollama

st.set_page_config(
    page_title="Clipping Anvisa com IA",
    layout="wide"
)

st.title("Clipping Anvisa com IA")
st.write("Resumo automático de notícias usando Ollama e Qwen.")

arquivo = st.file_uploader(
    "Envie o CSV com as notícias da Anvisa",
    type=["csv"]
)

if arquivo is not None:
    df = pd.read_csv(arquivo, sep=";")

    st.success(f"{len(df)} notícias carregadas.")

    if "resumo_ia" not in df.columns:
        df["resumo_ia"] = ""

    termo_busca = st.text_input("Buscar no título ou texto")

    if termo_busca:
        df_filtrado = df[
            df["titulo"].fillna("").str.contains(termo_busca, case=False, na=False)
            | df["texto"].fillna("").str.contains(termo_busca, case=False, na=False)
        ]
    else:
        df_filtrado = df.copy()

    st.write(f"{len(df_filtrado)} notícias encontradas.")

    if len(df_filtrado) > 0:
        titulos = df_filtrado["titulo"].tolist()

        titulo_escolhido = st.selectbox(
            "Escolha uma notícia para visualizar",
            titulos
        )

        noticia = df_filtrado[df_filtrado["titulo"] == titulo_escolhido].iloc[0]

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Notícia original")
            st.write(f"**Data:** {noticia.get('data', '')}")
            st.write(f"**Título:** {noticia.get('titulo', '')}")
            st.write(f"**Link:** {noticia.get('link', '')}")

            with st.expander("Ver texto completo"):
                st.write(noticia.get("texto", ""))

        with col2:
            st.subheader("Resumo com IA")

            modelo = st.selectbox(
                "Modelo Ollama",
                ["qwen3.5:0.8b", "gemma3:1b", "llama3.2:3b"]
            )

            prompt = f"""
            Analise a notícia abaixo e produza um resumo objetivo.

            Responda sempre em português do Brasil.

            Sua resposta deve começar diretamente com:

            Assunto principal:

            Não escreva nenhuma frase antes do assunto principal.
            Não escreva introdução.
            Não escreva "Okay", "Claro", "Aqui está o resumo" ou qualquer frase parecida.
            Não escreva comentários finais.

            Use obrigatoriamente este formato:

            Assunto principal:
            Resumo:
            Órgãos, produtos ou temas citados:
            Palavras-chave:

            Notícia:

            Título: {noticia.get("titulo", "")}

            Data: {noticia.get("data", "")}

Texto:
{noticia.get("texto", "")}
"""

            if st.button("Gerar resumo da notícia selecionada"):
                with st.spinner("Gerando resumo..."):
                    resposta = ollama.chat(
                        model=modelo,
                        messages=[
                             {
                                "role": "system",
                                "content": """
                        Você responde sempre em português do Brasil.

                        Você deve seguir exatamente o formato solicitado pelo usuário.
                        Não escreva introduções.
                        Não escreva frases como "Claro", "Okay", "Aqui está", "Segue o resumo" ou similares.
                        Não explique o que você está fazendo.
                        Não inclua comentários antes ou depois da resposta.
                        Comece diretamente pelo item 1.
                        """
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    )

                    resumo = resposta["message"]["content"]

                    indice_original = noticia.name
                    df.loc[indice_original, "resumo_ia"] = resumo

                    st.markdown(resumo)

            if st.button("Gerar resumo das notícias filtradas"):
                with st.spinner("Gerando resumos das notícias filtradas..."):

                    barra = st.progress(0)
                    total = len(df_filtrado)

                    for contador, (i, linha) in enumerate(df_filtrado.iterrows(), start=1):

                        prompt_lote = f"""
Analise a notícia abaixo e produza um resumo objetivo.

Responda sempre em português do Brasil.

Sua resposta deve começar diretamente com:

Assunto principal:

Não escreva nenhuma frase antes do assunto principal.
Não escreva introdução.
Não escreva "Okay", "Claro", "Aqui está o resumo" ou qualquer frase parecida.
Não escreva comentários finais.

Use obrigatoriamente este formato:

Assunto principal:
Resumo:
Órgãos, produtos ou temas citados:
Palavras-chave:

Notícia:

Título: {linha.get("titulo", "")}

Data: {linha.get("data", "")}

Texto:
{linha.get("texto", "")}
"""

                        resposta = ollama.chat(
                            model=modelo,
                            messages=[
                                {
                                    "role": "user",
                                    "content": prompt_lote
                                }
                            ]
                        )

                        resumo = resposta["message"]["content"]

                        df.loc[i, "resumo_ia"] = resumo

                        barra.progress(contador / total)

                st.success(f"Resumos gerados para {total} notícias filtradas.")

            if noticia.get("resumo_ia", ""):
                st.markdown("### Resumo salvo")
                st.markdown(noticia["resumo_ia"])

        st.divider()

        st.subheader("Base com resumos")

        st.dataframe(
            df[["data", "titulo", "link", "resumo_ia"]],
            use_container_width=True
        )

        csv = df.to_csv(index=False, sep=";", encoding="utf-8-sig")

        st.download_button(
            label="Baixar CSV com resumos",
            data=csv,
            file_name="noticias_anvisa_com_resumos.csv",
            mime="text/csv"
        )

    else:
        st.warning("Nenhuma notícia encontrada com esse termo.")

else:
    st.info("Envie o arquivo `noticias_anvisa_com_texto.csv` para começar.")