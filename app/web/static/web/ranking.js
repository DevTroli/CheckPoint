(function () {
  const tabela = document.getElementById("tabela-ranking");
  const corpo = document.getElementById("corpo-ranking");
  const vazio = document.getElementById("vazio");
  const voce = document.getElementById("voce");
  const dialogo = document.getElementById("dialogo");

  function linha(item, usuario) {
    const souEu = usuario && item.usuario_id === usuario.id;
    // nome_usuario vem vazio se a conta foi excluída; aí cai no número.
    const nomeBase = item.nome_usuario || "JOGADOR #" + item.usuario_id;
    const nome = souEu ? nomeBase + " (VOCÊ)" : nomeBase;
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
