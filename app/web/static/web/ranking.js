(function () {
  const tabela = document.getElementById("tabela-ranking");
  const corpo = document.getElementById("corpo-ranking");
  const vazio = document.getElementById("vazio");
  const voce = document.getElementById("voce");
  const dialogo = document.getElementById("dialogo");

  /* O ranking da API só traz usuario_id; só o nome do próprio usuário é conhecido. */
  function linha(item, usuario) {
    const souEu = usuario && item.usuario_id === usuario.id;
    const nome = souEu ? usuario.nome_usuario + " (VOCÊ)" : "JOGADOR #" + item.usuario_id;
    return Checkpoint.el(
      "tr",
      souEu ? { class: "destaque" } : {},
      Checkpoint.el("td", {}, String(item.posicao)),
      Checkpoint.el("td", {}, nome),
      Checkpoint.el("td", {}, String(item.xp))
    );
  }

  function resumoDoUsuario(gamificacao) {
    if (!gamificacao.posicao) return "VOCÊ AINDA NÃO TEM XP";
    const sep = Checkpoint.separador;
    return "VOCÊ: #" + gamificacao.posicao + sep + gamificacao.xp + " XP" + sep + "STREAK " + gamificacao.streak;
  }

  (async function iniciar() {
    try {
      const usuario = await Checkpoint.usuario();
      const resposta = await Checkpoint.api("GET", "/api/gamificacao/ranking/?limite=10");
      if (!resposta.ok) {
        Checkpoint.mostrarDialogo(dialogo, "Não foi possível carregar o ranking.");
        return;
      }
      corpo.replaceChildren(...resposta.dados.map((item) => linha(item, usuario)));
      tabela.hidden = resposta.dados.length === 0;
      vazio.hidden = resposta.dados.length > 0;

      if (usuario) {
        const gamificacao = await Checkpoint.gamificacao();
        if (gamificacao) {
          voce.textContent = resumoDoUsuario(gamificacao);
          voce.hidden = false;
        }
      }
    } catch (e) {
      Checkpoint.mostrarDialogo(dialogo, "Sem conexão com o servidor.");
    }
  })();
})();
