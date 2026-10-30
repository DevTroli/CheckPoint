(function () {
  const form = document.getElementById("form-auth");
  const dialogo = document.getElementById("dialogo");
  const botao = form.querySelector("button[type=submit]");
  const textoBotao = botao.textContent;

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    Checkpoint.limparErros(form, dialogo);
    botao.disabled = true;
    botao.textContent = "CARREGANDO...";

    const campos = Object.fromEntries(new FormData(form));
    try {
      if (form.dataset.acao === "cadastro") {
        const cadastro = await Checkpoint.api("POST", "/api/usuarios/", campos);
        if (!cadastro.ok) return Checkpoint.mostrarErro(form, dialogo, cadastro);
      }
      const login = await Checkpoint.api("POST", "/api/auth/login/", {
        email: campos.email,
        senha: campos.senha,
      });
      if (!login.ok) return Checkpoint.mostrarErro(form, dialogo, login);
      window.location.href = "/";
    } catch (e) {
      Checkpoint.mostrarDialogo(dialogo, "Sem conexão com o servidor.");
    } finally {
      botao.disabled = false;
      botao.textContent = textoBotao;
    }
  });
})();
