"""
Interface Tkinter completa do Monte Carlo PRO
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from concurrent.futures import ThreadPoolExecutor

from config import LOTTERIES, GenerationConfig, CUSTOS
from loader import carregar_historico, baixar_historico_cef
from analyzer import AnalisadorHistorico
from generator import gerar_jogos
from simulator import monte_carlo
from validator import validar_entrada_quantidade, validar_tipo_jogo
from utils.logger import logger
from utils.cache import history_cache


class MonteCarloPRO:
    """Interface principal da aplicação"""

    def __init__(self, root):
        self.root = root
        self.root.title("🎲 Monte Carlo PRO — Análise Histórica Avançada")
        self.root.geometry("1400x980")

        # Variáveis de estado
        self.tipo_jogo = tk.StringVar(value="Lotofácil")
        self.modo_geracao = tk.StringVar(value="Automático")
        self.modo_risco = tk.StringVar(value="Conservador")

        self.usar_paridade = tk.BooleanVar(value=True)
        self.pares_desejados = tk.IntVar(value=7)
        self.impares_desejados = tk.IntVar(value=8)

        self.usar_tendencia = tk.BooleanVar(value=True)
        self.usar_soma = tk.BooleanVar(value=True)
        self.usar_consecutivos = tk.BooleanVar(value=True)
        self.usar_coocorrencia = tk.BooleanVar(value=False)
        self.max_consecutivos = tk.IntVar(value=3)
        self.pct_quentes = tk.IntVar(value=60)

        self.usar_casas = tk.BooleanVar(value=False)
        self.max_casas_fora = tk.IntVar(value=2)

        self.dezenas_vars = {}
        self.executor = ThreadPoolExecutor(max_workers=2)

        self._criar_interface()
        self._on_tipo_change()

        logger.info("Aplicação iniciada")

    def _criar_interface(self):
        """Cria interface Tkinter"""
        # Canvas com scrollbar
        canvas = tk.Canvas(self.root)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas)
        frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Título
        tk.Label(
            frame,
            text="🎲 Monte Carlo PRO — Análise Histórica Avançada",
            font=("Arial", 14, "bold"),
            fg="darkblue",
        ).pack(pady=6)

        # Top controls
        f_top = tk.Frame(frame)
        f_top.pack(fill="x", padx=10, pady=2)

        tk.Label(f_top, text="Jogo:", font=("Arial", 10, "bold")).grid(
            row=0, column=0
        )
        tk.OptionMenu(
            f_top, self.tipo_jogo, *LOTTERIES.keys(), command=lambda _: self._on_tipo_change()
        ).grid(row=0, column=1, padx=4)

        tk.Label(f_top, text="Geração:", font=("Arial", 10, "bold")).grid(
            row=0, column=2, padx=(16, 0)
        )
        tk.Radiobutton(
            f_top, text="Manual", variable=self.modo_geracao, value="Manual"
        ).grid(row=0, column=3)
        tk.Radiobutton(
            f_top, text="Automático", variable=self.modo_geracao, value="Automático"
        ).grid(row=0, column=4)

        tk.Label(f_top, text="Risco:", font=("Arial", 10, "bold")).grid(
            row=0, column=5, padx=(16, 0)
        )
        tk.Radiobutton(
            f_top, text="Conservador", variable=self.modo_risco, value="Conservador"
        ).grid(row=0, column=6)
        tk.Radiobutton(
            f_top, text="Agressivo", variable=self.modo_risco, value="Agressivo"
        ).grid(row=0, column=7)

        tk.Button(
            f_top, text="⬇️ Baixar CEF", bg="steelblue", fg="white",
            command=self._download_cef
        ).grid(row=0, column=8, padx=4)

        self.lbl_status = tk.Label(frame, text="", fg="gray", font=("Arial", 9))
        self.lbl_status.pack()

        # Dezenas
        self.frame_dezenas = tk.LabelFrame(frame, text="Seleção Manual de Dezenas")
        self.frame_dezenas.pack(pady=4, padx=10, fill="x")

        # Filtros
        f_fil = tk.LabelFrame(frame, text="Filtros Avançados")
        f_fil.pack(pady=4, padx=10, fill="x")

        tk.Checkbutton(
            f_fil, text="✅ Paridade", variable=self.usar_paridade
        ).grid(row=0, column=0, sticky="w")
        tk.Label(f_fil, text="Pares:").grid(row=0, column=1)
        tk.Entry(f_fil, textvariable=self.pares_desejados, width=4).grid(
            row=0, column=2
        )
        tk.Label(f_fil, text="Ímpares:").grid(row=0, column=3)
        tk.Entry(f_fil, textvariable=self.impares_desejados, width=4).grid(
            row=0, column=4
        )

        tk.Checkbutton(
            f_fil, text="📈 Tendência", variable=self.usar_tendencia
        ).grid(row=0, column=5, padx=10)
        tk.Checkbutton(
            f_fil, text="∑ Soma Q1-Q3", variable=self.usar_soma
        ).grid(row=0, column=6, padx=6)
        tk.Checkbutton(
            f_fil, text="🔗 Co-ocorrência", variable=self.usar_coocorrencia
        ).grid(row=0, column=7, padx=6)

        tk.Checkbutton(
            f_fil, text="🔢 Consecutivos (máx:)", variable=self.usar_consecutivos
        ).grid(row=1, column=0, columnspan=2, sticky="w")
        tk.Entry(f_fil, textvariable=self.max_consecutivos, width=3).grid(
            row=1, column=2
        )

        tk.Label(f_fil, text="🌡️ % Quentes:").grid(row=1, column=3, padx=(16, 0))
        tk.Scale(
            f_fil, from_=0, to=100, orient="horizontal",
            variable=self.pct_quentes, length=180
        ).grid(row=1, column=4, columnspan=3, sticky="w")
        tk.Label(f_fil, textvariable=self.pct_quentes, width=4).grid(row=1, column=7)

        # Execução
        f_exec = tk.Frame(frame)
        f_exec.pack(pady=6)

        tk.Label(f_exec, text="Qtd. jogos:").pack(side="left")
        self.entry_qtd = tk.Entry(f_exec, width=6)
        self.entry_qtd.insert(0, "60")
        self.entry_qtd.pack(side="left", padx=4)

        tk.Button(
            f_exec, text="🎯 Gerar e Analisar", command=self._executar,
            bg="darkgreen", fg="white", font=("Arial", 11, "bold"),
            height=2, padx=20
        ).pack(side="left", padx=8)

        tk.Button(
            f_exec, text="📊 Análise Histórica", command=self._abrir_analise,
            bg="navy", fg="white", font=("Arial", 10), height=2
        ).pack(side="left", padx=4)

        # Saída
        f_saida = tk.LabelFrame(frame, text="🏆 Resultados")
        f_saida.pack(pady=8, padx=10, fill="both", expand=True)

        sb_out = tk.Scrollbar(f_saida)
        sb_out.pack(side=tk.RIGHT, fill=tk.Y)
        self.saida = tk.Text(
            f_saida, width=160, height=22, yscrollcommand=sb_out.set,
            font=("Courier", 9)
        )
        self.saida.pack(side=tk.LEFT, fill="both", expand=True)
        sb_out.config(command=self.saida.yview)

    def _on_tipo_change(self):
        """Atualiza interface ao mudar tipo de jogo"""
        history_cache.clear()
        self._atualizar_dezenas()
        tipo = self.tipo_jogo.get()
        k = LOTTERIES[tipo].k_jogo
        self.pares_desejados.set(k // 2)
        self.impares_desejados.set(k - k // 2)

    def _atualizar_dezenas(self):
        """Atualiza grid de dezenas"""
        for w in self.frame_dezenas.winfo_children():
            w.destroy()
        self.dezenas_vars.clear()

        tipo = self.tipo_jogo.get()
        min_n = LOTTERIES[tipo].min
        max_n = LOTTERIES[tipo].max

        for i in range(min_n, max_n + 1):
            var = tk.BooleanVar()
            self.dezenas_vars[i] = var
            tk.Checkbutton(
                self.frame_dezenas, text=str(i).zfill(2), variable=var, width=4
            ).grid(row=(i - min_n) // 10, column=(i - min_n) % 10)

    def _download_cef(self):
        """Baixa histórico da CEF"""
        tipo = self.tipo_jogo.get()
        self.lbl_status.config(text=f"⏳ Baixando {tipo}...", fg="orange")
        self.root.update()

        def _run():
            ok, msg = baixar_historico_cef(tipo)
            if ok:
                self.root.after(
                    0,
                    lambda: self.lbl_status.config(
                        text=f"✅ {msg}", fg="green"
                    ),
                )
            else:
                self.root.after(
                    0,
                    lambda: self.lbl_status.config(
                        text=f"❌ Erro: {msg}", fg="red"
                    ),
                )

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _executar(self):
        """Executa geração e análise"""
        self.saida.delete("1.0", tk.END)
        self.saida.insert(tk.END, "⏳ Gerando jogos...\n")
        self.root.update()

        # Validar entrada
        válido, erro, qtd = validar_entrada_quantidade(self.entry_qtd.get())
        if not válido:
            messagebox.showerror("Erro", erro)
            return

        tipo = self.tipo_jogo.get()
        válido, erro = validar_tipo_jogo(tipo)
        if not válido:
            messagebox.showerror("Erro", erro)
            return

        # Montar configuração
        dezenas_sel = [n for n, v in self.dezenas_vars.items() if v.get()]
        config = GenerationConfig(
            tipo=tipo,
            qtd=qtd,
            modo_geracao=self.modo_geracao.get(),
            modo_risco=self.modo_risco.get(),
            usar_paridade=self.usar_paridade.get(),
            pares_desejados=self.pares_desejados.get(),
            impares_desejados=self.impares_desejados.get(),
            usar_tendencia=self.usar_tendencia.get(),
            usar_soma=self.usar_soma.get(),
            usar_consecutivos=self.usar_consecutivos.get(),
            usar_coocorrencia=self.usar_coocorrencia.get(),
            max_consecutivos=self.max_consecutivos.get(),
            pct_quentes=self.pct_quentes.get(),
            usar_casas=self.usar_casas.get(),
            max_casas_fora=self.max_casas_fora.get(),
            dezenas_selecionadas=dezenas_sel,
        )

        def _run():
            try:
                # Gerar
                jogos, erro = gerar_jogos(config)
                if not jogos:
                    self.root.after(
                        0,
                        lambda: messagebox.showerror("Erro", erro),
                    )
                    return

                # Analisar
                an = AnalisadorHistorico(tipo)
                ranking = monte_carlo(
                    jogos, tipo, config.modo_risco, an
                )
                resumo = an.resumo()

                # Exibir
                self.root.after(0, lambda: self._exibir_resultados(
                    ranking, resumo, qtd, config, tipo
                ))

            except Exception as e:
                logger.exception(f"Erro na execução: {e}")
                self.root.after(
                    0,
                    lambda: messagebox.showerror("Erro", str(e)),
                )

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _exibir_resultados(self, ranking, resumo, qtd, config, tipo):
        """Exibe resultados da análise"""
        self.saida.delete("1.0", tk.END)

        # Cabeçalho
        self.saida.insert(
            tk.END, "=" * 150 + "\n"
        )
        self.saida.insert(
            tk.END,
            f"  🏆 TOP {len(ranking)} — {tipo} | "
            f"{config.modo_geracao} | {config.modo_risco}\n",
        )

        if resumo:
            self.saida.insert(
                tk.END,
                f"  📊 {resumo['n']} sorteios | Soma Q1-Q3: "
                f"{resumo['soma_q1']}–{resumo['soma_q3']} "
                f"(média {resumo['soma_media']}) | Pares médio: "
                f"{resumo['pares_media']} | Consec. médio: "
                f"{resumo['consec_media']} | Repetições: "
                f"{resumo['rep_media']}\n"
                f"  🔥 Quentes: {resumo['top5_quentes']}   "
                f"❄️ Frios: {resumo['top5_frios']}\n",
            )

        self.saida.insert(tk.END, "=" * 150 + "\n")
        self.saida.insert(
            tk.END,
            f"{'#':>3} | {'Jogo':^65} | {'Média':>6} | {'Desvio':>6} | "
            f"{'Máx':>4} | {'Prob':>6} | {'HScore':>7} | {'Score':>8} | "
            f"{'EV R$':>8} | {'EV%':>6}\n",
        )
        self.saida.insert(tk.END, "-" * 150 + "\n")

        for i, r in enumerate(ranking, 1):
            jogo_str = " ".join(str(n).zfill(2) for n in r["jogo"])
            self.saida.insert(
                tk.END,
                f"{i:>3} | {jogo_str:^65} | {r['media']:>6} | "
                f"{r['desvio']:>6} | {r['max']:>4} | {r['prob']:>6} | "
                f"{r['hist_score']:>7} | {r['score']:>8} | "
                f"{r['ev']:>8.2f} | {r['ev_pct']:>5.1f}%\n",
            )

        self.lbl_status.config(
            text=f"✅ {qtd} jogos gerados → {len(ranking)} selecionados.",
            fg="green",
        )

    def _abrir_analise(self):
        """Abre janela de análise histórica"""
        tipo = self.tipo_jogo.get()
        an = AnalisadorHistorico(tipo)

        if not an.historico:
            messagebox.showwarning(
                "Sem dados",
                f"Não há histórico para {tipo}.\nClique em '⬇️ Baixar CEF'.",
            )
            return

        win = tk.Toplevel(self.root)
        win.title(f"📊 Análise Histórica — {tipo}")
        win.geometry("960x720")

        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=6, pady=6)

        # Aba 1: Frequência
        tab1 = tk.Frame(nb)
        nb.add(tab1, text="🔥 Frequência & Atraso")

        sb1 = tk.Scrollbar(tab1)
        sb1.pack(side=tk.RIGHT, fill=tk.Y)
        t1 = tk.Text(tab1, font=("Courier", 9), yscrollcommand=sb1.set)
        t1.pack(fill="both", expand=True)
        sb1.config(command=t1.yview)

        cfg = LOTTERIES[tipo]
        t1.insert(
            tk.END,
            f"FREQUÊNCIA & ATRASO — {tipo} ({an.n} sorteios)\n"
            f"{'='*75}\n"
            f"{'Num':>4} | {'Freq%':>6} | {'Contagem':>8} | "
            f"{'Atraso':>6} | {'Score':>7} | {'Status':>10} | Barra\n"
            f"{'-'*75}\n",
        )

        for n in range(cfg.min, cfg.max + 1):
            freq_pct = an.frequencia.get(n, 0) * 100
            contagem = round(freq_pct / 100 * an.n)
            atraso = an.atraso.get(n, 0)
            score = an.score_numero.get(n, 0)
            status = (
                "🔥 QUENTE"
                if n in an.quentes
                else ("❄️ FRIO" if n in an.frios else "🌡️ NORMAL")
            )
            barra = "█" * min(40, int(freq_pct * 2))
            t1.insert(
                tk.END,
                f"{str(n).zfill(2):>4} | {freq_pct:>5.1f}% | {contagem:>8} | "
                f"{atraso:>6} | {score:>7.5f} | {status:>10} | {barra}\n",
            )

        # Aba 2: Estatísticas
        tab2 = tk.Frame(nb)
        nb.add(tab2, text="📈 Estatísticas")

        sb2 = tk.Scrollbar(tab2)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)
        t2 = tk.Text(tab2, font=("Courier", 9), yscrollcommand=sb2.set)
        t2.pack(fill="both", expand=True)
        sb2.config(command=t2.yview)

        t2.insert(
            tk.END,
            f"ESTATÍSTICAS GERAIS — {tipo} ({an.n} sorteios)\n"
            f"{'='*60}\n\n"
            f"SOMA TOTAL DOS SORTEIOS:\n"
            f"  Média:       {an.stats_soma['media']:.1f}\n"
            f"  Desvio:      {an.stats_soma['desvio']:.1f}\n"
            f"  Q1 – Q3:     {an.stats_soma['q1']} – {an.stats_soma['q3']}\n"
            f"  Min – Max:   {an.stats_soma['min']} – {an.stats_soma['max']}\n\n"
            f"PARIDADE (quantidade de números pares):\n"
            f"  Média:       {an.stats_pares['media']:.1f}\n"
            f"  Desvio:      {an.stats_pares['desvio']:.1f}\n"
            f"  Range típico: {round(an.stats_pares['media'] - an.stats_pares['desvio'])} – "
            f"{round(an.stats_pares['media'] + an.stats_pares['desvio'])}\n\n"
            f"SEQUÊNCIAS CONSECUTIVAS:\n"
            f"  Média:       {an.stats_consec['media']:.1f}\n"
            f"  Desvio:      {an.stats_consec['desvio']:.1f}\n"
            f"  Máx histórico: {an.stats_consec['max']}\n\n"
            f"REPETIÇÕES ENTRE SORTEIOS:\n"
            f"  Média:       {an.ciclo['media_repeticao']}\n"
            f"  Desvio:      {an.ciclo['desvio']}\n",
        )

        # Aba 3: Co-ocorrência
        tab3 = tk.Frame(nb)
        nb.add(tab3, text="🔗 Co-ocorrência")

        sb3 = tk.Scrollbar(tab3)
        sb3.pack(side=tk.RIGHT, fill=tk.Y)
        t3 = tk.Text(tab3, font=("Courier", 9), yscrollcommand=sb3.set)
        t3.pack(fill="both", expand=True)
        sb3.config(command=t3.yview)

        t3.insert(
            tk.END,
            f"TOP 40 PARES MAIS FREQUENTES — {tipo}\n"
            f"{'='*60}\n\n"
            f"{'Par':>8} | {'Aparições':>9} | {'Freq%':>6} | Barra\n"
            f"{'-'*60}\n",
        )

        for (a, b), cnt in an.top_pares(40):
            pct = cnt / an.n * 100
            barra = "█" * min(40, int(pct * 3))
            t3.insert(
                tk.END,
                f"  {str(a).zfill(2)}-{str(b).zfill(2)} | {cnt:>9} | "
                f"{pct:>5.1f}% | {barra}\n",
            )


def main():
    """Função principal"""
    root = tk.Tk()
    app = MonteCarloPRO(root)
    root.mainloop()


if __name__ == "__main__":
    main()
