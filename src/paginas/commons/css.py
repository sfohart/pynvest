
import streamlit.components.v1 as components

# Detecta e salva o tema no sessionStorage (executado no front)
def detectar_tema_streamlit():
    components.html("""
        <script>
            const tema = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            window.sessionStorage.setItem("tema_streamlit", tema);
        </script>
    """, height=0)

# Lê o tema armazenado no sessionStorage via document.write (retorna como string)
def obter_tema_streamlit():
    return components.html("""
        <script>
            const tema = window.sessionStorage.getItem("tema_streamlit") || "light";
            document.write(tema);
        </script>
    """, height=0)