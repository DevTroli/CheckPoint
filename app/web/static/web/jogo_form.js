(function () {
  const form = document.getElementById("form-jogo");
  const dialogo = document.getElementById("dialogo");
  const botao = form.querySelector("button[type=submit]");
  const jogoId = form.dataset.jogoId;
  const textoBotao = botao.textContent;
  const campos = ["nome", "categoria", "data_lancamento", "desenvolvedora", "publicadora", "descricao"];

  async function iniciar() {
    const usuario = await Checkpoint.usuario();
    if (!usuario || usuario.papel !== "admin") {
      window.location.href = "/jogos/";
      return;
    }
    if (!jogoId) return;
    const resposta = await Checkpoint.api("GET", "/api/jogos/" + jogoId + "/");
    if (!resposta.ok) {
      Checkpoint.mostrarDialogo(dialogo, resposta.dados.mensagem || "Jogo não encontrado.");
      botao.disabled = true;
      return;
    }
    campos.forEach((campo) => (form.elements[campo].value = resposta.dados[campo] || ""));
  }

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    Checkpoint.limparErros(form, dialogo);
    botao.disabled = true;
    botao.textContent = "SALVANDO...";

    const corpo = Object.fromEntries(campos.map((campo) => [campo, form.elements[campo].value.trim()]));
    try {
      const resposta = jogoId
        ? await Checkpoint.api("PUT", "/api/jogos/" + jogoId + "/", corpo)
        : await Checkpoint.api("POST", "/api/jogos/", corpo);
      if (!resposta.ok) return Checkpoint.mostrarErro(form, dialogo, resposta);
      window.location.href = "/jogos/" + resposta.dados.id + "/";
    } catch (e) {
      Checkpoint.mostrarDialogo(dialogo, "Sem conexão com o servidor.");
    } finally {
      botao.disabled = false;
      botao.textContent = textoBotao;
    }
  });

  iniciar().catch(() => Checkpoint.mostrarDialogo(dialogo, "Sem conexão com o servidor."));
})();
