(function () {
  const lista = document.getElementById("lista-jogos");
  const vazio = document.getElementById("vazio");
  const dialogo = document.getElementById("dialogo");
  const busca = document.getElementById("busca");
  const categoria = document.getElementById("categoria");
  const ordenar = document.getElementById("ordenar");

  function cartao(jogo) {
    const meta = [Checkpoint.ano(jogo.data_lancamento), jogo.desenvolvedora]
      .filter(Boolean)
      .join(" | ");
    return Checkpoint.el(
      "li",
      { class: "cartao" },
      Checkpoint.el(
        "a",
        { class: "cartao-link", href: "/jogos/" + jogo.id + "/" },
        Checkpoint.el("span", { class: "tag" }, jogo.categoria),
        Checkpoint.el("h2", { class: "cartao-nome" }, jogo.nome),
        Checkpoint.el("p", { class: "cartao-meta" }, meta)
      )
    );
  }

  async function carregar() {
    const params = new URLSearchParams();
    if (busca.value.trim()) params.set("busca", busca.value.trim());
    if (categoria.value) params.set("categoria", categoria.value);
    params.set("ordenar", ordenar.value);

    const resposta = await Checkpoint.api("GET", "/api/jogos/?" + params);
    if (!resposta.ok) {
      Checkpoint.mostrarDialogo(dialogo, "Não foi possível carregar o catálogo.");
      return resposta;
    }
    dialogo.hidden = true;
    const jogos = resposta.dados;
    lista.replaceChildren(...jogos.map(cartao));
    vazio.hidden = jogos.length > 0;
    return resposta;
  }

  function preencherCategorias(jogos) {
    const nomes = [...new Set(jogos.map((jogo) => jogo.categoria))].sort();
    nomes.forEach((nome) => categoria.append(Checkpoint.el("option", { value: nome }, nome)));
  }

  let espera = null;
  busca.addEventListener("input", () => {
    clearTimeout(espera);
    espera = setTimeout(carregar, 250);
  });
  categoria.addEventListener("change", carregar);
  ordenar.addEventListener("change", carregar);

  (async function iniciar() {
    try {
      const inicial = await carregar();
      if (inicial.ok) preencherCategorias(inicial.dados);
      const usuario = await Checkpoint.usuario();
      if (usuario && usuario.papel === "admin") {
        document.getElementById("novo-jogo").hidden = false;
      }
    } catch (e) {
      Checkpoint.mostrarDialogo(dialogo, "Sem conexão com o servidor.");
    }
  })();
})();
