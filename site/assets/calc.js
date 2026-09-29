// Calcolatori ContiChiari. Tutto gira nel browser: nessun dato viene inviato.
(function () {
  var eur = new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });
  function num(id) { var v = parseFloat(String(document.getElementById(id).value).replace(",", ".")); return isNaN(v) ? 0 : v; }
  function set(id, v) { var el = document.getElementById(id); if (el) el.textContent = typeof v === "number" ? eur.format(v) : v; }
  function show(id, on) { var el = document.getElementById(id); if (el) el.classList.toggle("hidden", !on); }

  // Contributi INPS nel forfettario in base alla gestione scelta.
  function contributi(reddito, g) {
    if (g.tipo === "separata" || g.tipo === "cassa") return reddito * g.aliquota;
    var c = g.fisso + Math.max(0, reddito - g.minimale) * g.aliquota;
    return g.riduzione ? c * 0.65 : c;
  }

  // --- Calcolatore tasse forfettario ---
  var ff = document.getElementById("calc-forfettario");
  if (ff) {
    var gestione = document.getElementById("gestione");
    var syncGestione = function () {
      var t = gestione.value;
      show("box-percentuale", t === "separata" || t === "cassa");
      show("box-artcomm", t === "artigiani" || t === "commercianti");
      if (t === "separata") document.getElementById("aliq").value = "26.07";
      if (t === "artigiani") { document.getElementById("fisso").value = "4460"; document.getElementById("aliqArt").value = "24"; }
      if (t === "commercianti") { document.getElementById("fisso").value = "4550"; document.getElementById("aliqArt").value = "24.48"; }
    };
    gestione.addEventListener("change", function () { syncGestione(); run(); });
    var run = function () {
      var ricavi = num("ricavi"), coeff = num("coeff") / 100, imp = num("imposta") / 100, t = gestione.value;
      var g = (t === "separata" || t === "cassa")
        ? { tipo: t, aliquota: num("aliq") / 100 }
        : { tipo: t, fisso: num("fisso"), minimale: num("minimale"), aliquota: num("aliqArt") / 100, riduzione: document.getElementById("riduzione").checked };
      var reddito = ricavi * coeff;
      var inps = contributi(reddito, g);
      var imponibile = Math.max(0, reddito - inps);
      var tasse = imponibile * imp;
      var netto = ricavi - inps - tasse;
      set("r-reddito", reddito); set("r-inps", inps); set("r-imponibile", imponibile);
      set("r-tasse", tasse); set("r-netto", netto); set("r-mese", (inps + tasse) / 12);
      set("r-perc", ricavi > 0 ? ((inps + tasse) / ricavi * 100).toFixed(1).replace(".", ",") + "%" : "–");
      show("r-limite", ricavi > 85000);
    };
    ff.addEventListener("input", run);
    syncGestione(); run();
  }

  // --- Tariffa oraria freelance (forfettario, gestione separata) ---
  var tf = document.getElementById("calc-tariffa");
  if (tf) {
    var runT = function () {
      var netto = num("t-netto"), spese = num("t-spese"), ore = num("t-ore"), sett = num("t-sett");
      var c = num("t-coeff") / 100, a = num("t-imposta") / 100, s = num("t-inps") / 100;
      var den = 1 - c * s - c * (1 - s) * a;
      var fatturato = den > 0 ? (netto + spese) / den : 0;
      var oreTot = ore * sett;
      set("t-fatturato", fatturato);
      set("t-oraria", oreTot > 0 ? fatturato / oreTot : 0);
      set("t-giorno", oreTot > 0 ? fatturato / oreTot * 8 : 0);
      set("t-mese", fatturato / 12);
      show("t-limite", fatturato > 85000);
    };
    tf.addEventListener("input", runT); runT();
  }

  // --- Netto prestazione occasionale ---
  var po = document.getElementById("calc-occasionale");
  if (po) {
    var runP = function () {
      var lordo = num("p-lordo"), gia = num("p-gia"), sost = document.getElementById("p-sostituto").checked;
      var aliq = num("p-inps") / 100;
      var ritenuta = sost ? lordo * 0.2 : 0;
      var eccedenza = Math.max(0, gia + lordo - 5000) - Math.max(0, gia - 5000);
      var inpsTuo = eccedenza * aliq / 3;
      set("p-ritenuta", ritenuta); set("p-inpsval", inpsTuo);
      set("p-netto", lordo - ritenuta - inpsTuo);
      set("p-bollo", lordo > 77.47 ? "Sì, 2 €" : "No");
      show("p-soglia", gia + lordo > 5000);
    };
    po.addEventListener("input", runP); runP();
  }
})();
