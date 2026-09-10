-- BIOCOL001 / Ictiofauna
-- Proposta de tabela detalhe para biometria e reproducao.
-- Revisar antes de executar em producao.

CREATE TABLE IF NOT EXISTS public.resultados_ictiofauna_detalhe (
    id_resultado_ictio_detalhe BIGSERIAL PRIMARY KEY,
    id_resultado_ictio INTEGER NOT NULL
        REFERENCES public.resultados_ictiofauna(id_resultado_ictio)
        ON DELETE CASCADE,
    id_esforco INTEGER NOT NULL
        REFERENCES public.esforcos_amostragem(id_esforco),
    id_especie INTEGER NOT NULL
        REFERENCES public.especies(id_especie),
    codigo_opyta TEXT,
    linha_fonte INTEGER,
    ponto TEXT,
    campanha TEXT,
    metodo_de_captura TEXT,
    tipo_de_amostragem TEXT,
    malha_ou_anzol TEXT,
    numero_de_individuos NUMERIC,
    ct_cm NUMERIC,
    cp_cm NUMERIC,
    pc_g NUMERIC,
    sexo_raw TEXT,
    sexo_padronizado TEXT,
    emg_raw TEXT,
    emg_codigo TEXT,
    emg_estadio TEXT,
    emg_ordem NUMERIC,
    evidencia_reprodutiva_forte BOOLEAN,
    observacao_individuo_lote TEXT,
    source_workbook TEXT,
    source_sheet TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_res_ictio_det_resultado
    ON public.resultados_ictiofauna_detalhe(id_resultado_ictio);

CREATE INDEX IF NOT EXISTS idx_res_ictio_det_esforco_especie
    ON public.resultados_ictiofauna_detalhe(id_esforco, id_especie);

CREATE INDEX IF NOT EXISTS idx_res_ictio_det_codigo_opyta
    ON public.resultados_ictiofauna_detalhe(codigo_opyta);

CREATE INDEX IF NOT EXISTS idx_res_ictio_det_repro
    ON public.resultados_ictiofauna_detalhe(sexo_padronizado, emg_codigo);

