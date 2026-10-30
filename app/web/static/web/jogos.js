(function () {
  const lista = document.getElementById("lista-jogos");
  const vazio = document.getElementById("vazio");
  const dialogo = document.getElementById("dialogo");
  const busca = document.getElementById("busca");
  const categoria = document.getElementById("categoria");
  const ordenar = document.getElementById("ordenar");
  const visao = document.getElementById("visao");

  let usuario = null;
  let registros = new Map(); // jogo_id -> registro do usuário logado

  function trecho(texto) {
    const limpo = String(texto || "").trim();
    return limpo.length > 90 ? limpo.slice(0, 90).trimEnd() + "..." : limpo;
  }

  /* Caixa quadrada à direita do card com a nota do usuário. */
  function caixaNota(registro) {
    const nota = Number(registro.nota);
    return Checkpoint.el(
      "div",
      { class: "caixa-nota", "aria-label": nota > 0 ? "Nota " + nota + " de 10" : "Sem nota" },
      Checkpoint.el("span", { class: "caixa-nota-valor" }, nota > 0 ? String(nota) : "-")
    );
  }

  function detalhesAvaliacao(registro) {
    if (registro) {
      const filhos = [
        Checkpoint.el("p", { class: "cartao-tempo" }, Checkpoint.formatarTempo(registro.tempo_jogado_minutos)),
      ];
      if (registro.avaliacao) {
        filhos.push(Checkpoint.el("p", { class: "cartao-texto" }, trecho(registro.avaliacao)));
      }
      return filhos;
    }
    return usuario ? [Checkpoint.el("p", { class: "cartao-avaliar" }, "AVALIAR >")] : [];
  }

  function cartao(jogo) {
    const registro = registros.get(jogo.id);
    const meta = [Checkpoint.ano(jogo.data_lancamento), jogo.desenvolvedora]
      .filter(Boolean)
      .join(" | ");
    const corpo = Checkpoint.el(
      "div",
      { class: "cartao-corpo" },
      Checkpoint.el("span", { class: "tag" }, jogo.categoria),
      Checkpoint.el("h2", { class: "cartao-nome" }, jogo.nome),
      Checkpoint.el("p", { class: "cartao-meta" }, meta),
      ...detalhesAvaliacao(registro)
    );
    const filhos = registro ? [corpo, caixaNota(registro)] : [corpo];
    return Checkpoint.el(
      "li",
      { class: "cartao" },
      Checkpoint.el("a", { class: "cartao-link", href: "/jogos/" + jogo.id + "/" }, ...filhos)
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
    const somenteMeus = usuario && visao.value === "meus";
    const jogos = somenteMeus ? resposta.dados.filter((jogo) => registros.has(jogo.id)) : resposta.dados;
    lista.replaceChildren(...jogos.map(cartao));
    vazio.textContent = somenteMeus && !registros.size ? "VOCÊ AINDA NÃO AVALIOU NENHUM JOGO" : "NENHUM JOGO ENCONTRADO";
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
  visao.addEventListener("change", carregar);

  (async function iniciar() {
    try {
      usuario = await Checkpoint.usuario();
      if (usuario) {
        const meus = await Checkpoint.api("GET", "/api/registros/");
        if (meus.ok) registros = new Map(meus.dados.map((registro) => [registro.jogo_id, registro]));
        visao.value = registros.size ? "meus" : "todos";
        document.getElementById("campo-visao").hidden = false;
        if (usuario.papel === "admin") document.getElementById("novo-jogo").hidden = false;
      }
      const inicial = await carregar();
      if (inicial.ok) preencherCategorias(inicial.dados);
    } catch (e) {
      Checkpoint.mostrarDialogo(dialogo, "Sem conexão com o servidor.");
    }
  })();
})();
