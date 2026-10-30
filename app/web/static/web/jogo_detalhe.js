(function () {
  const jogoId = document.getElementById("detalhe").dataset.jogoId;
  const dialogo = document.getElementById("dialogo");
  const artigo = document.getElementById("jogo");
  const confirmar = document.getElementById("confirmar");

  function texto(id, valor, padrao) {
    document.getElementById(id).textContent = valor || padrao || "";
  }

  async function iniciar() {
    try {
      const resposta = await Checkpoint.api("GET", "/api/jogos/" + jogoId + "/");
      if (!resposta.ok) {
        Checkpoint.mostrarDialogo(dialogo, resposta.dados.mensagem || "Jogo não encontrado.");
        return;
      }
      const jogo = resposta.dados;
      document.title = jogo.nome + " | Checkpoint";
      texto("jogo-nome", jogo.nome);
      texto("jogo-categoria", jogo.categoria);
      texto("jogo-ano", Checkpoint.ano(jogo.data_lancamento), "-");
      texto("jogo-desenvolvedora", jogo.desenvolvedora, "-");
      texto("jogo-publicadora", jogo.publicadora, "-");
      texto("jogo-descricao", jogo.descricao, "Sem descrição.");
      artigo.hidden = false;

      const usuario = await Checkpoint.usuario();
      if (usuario && usuario.papel === "admin") {
        document.getElementById("editar").href = "/jogos/" + jogoId + "/editar/";
        document.getElementById("acoes-admin").hidden = false;
      }
    } catch (e) {
      Checkpoint.mostrarDialogo(dialogo, "Sem conexão com o servidor.");
    }
  }

  document.getElementById("excluir").addEventListener("click", () => {
    confirmar.hidden = false;
  });
  document.getElementById("confirmar-nao").addEventListener("click", () => {
    confirmar.hidden = true;
  });
  document.getElementById("confirmar-sim").addEventListener("click", async () => {
    try {
      const resposta = await Checkpoint.api("DELETE", "/api/jogos/" + jogoId + "/");
      if (!resposta.ok) {
        confirmar.hidden = true;
        Checkpoint.mostrarDialogo(dialogo, resposta.dados.mensagem || "Não foi possível excluir.");
        return;
      }
      window.location.href = "/jogos/";
    } catch (e) {
      Checkpoint.mostrarDialogo(dialogo, "Sem conexão com o servidor.");
    }
  });

  iniciar();
})();
