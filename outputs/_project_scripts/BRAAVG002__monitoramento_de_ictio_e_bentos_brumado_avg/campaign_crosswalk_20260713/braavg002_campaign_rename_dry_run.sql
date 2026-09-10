-- BRAAVG002 campaign rename dry-run / template.
-- NAO EXECUTAR sem Gate A/B explicito e backup aprovado.
WITH mapa(id_campanha, nome_atual, nome_padrao) AS (
  VALUES
    (49, '1ª-Ago-22', 'C001-2022-08-SC'),
    (50, '2ª-Set-22', 'C002-2022-09-SC'),
    (51, '3ª-Out-22', 'C003-2022-10-CH'),
    (14, '4ª-Nov-22', 'C004-2022-11-CH'),
    (52, '5ª-Dez-22', 'C005-2022-12-CH'),
    (16, '6ª-Jan-23', 'C006-2023-01-CH'),
    (53, '7ª-Fev-23', 'C007-2023-02-CH'),
    (18, '8ª-Mar-23', 'C008-2023-03-CH'),
    (54, '9ª-Abr-23', 'C009-2023-04-SC'),
    (55, '10ª-Mai-23', 'C010-2023-05-SC'),
    (21, '11ª-Jun-23', 'C011-2023-06-SC'),
    (22, '12ª-Jul-23', 'C012-2023-07-SC'),
    (56, '13ª-Ago-23', 'C013-2023-08-SC'),
    (57, '14ª-Set-23', 'C014-2023-09-SC'),
    (58, '15ª-Out-23', 'C015-2023-10-CH'),
    (26, '16ª-Nov-23', 'C016-2023-11-CH'),
    (59, '17ª-Dez-23', 'C017-2023-12-CH'),
    (28, '18ª-Jan-24', 'C018-2024-01-CH'),
    (60, '19ª-Fev-24', 'C019-2024-02-CH'),
    (30, '20ª-Mar-24', 'C020-2024-03-CH'),
    (61, '21ª-Abr-24', 'C021-2024-04-SC'),
    (62, '22ª-Mai-24', 'C022-2024-05-SC'),
    (33, '23ª-Jun-24', 'C023-2024-06-SC'),
    (34, '24ª-Jul-24', 'C024-2024-07-SC'),
    (63, '25ª-Ago-24', 'C025-2024-08-SC'),
    (64, '26ª-Set-24', 'C026-2024-09-SC'),
    (65, '27ª-Out-24', 'C027-2024-10-CH'),
    (38, '28ª-Nov-24', 'C028-2024-11-CH'),
    (66, '29ª-Dez-24', 'C029-2024-12-CH'),
    (40, '30ª-Jan-25', 'C030-2025-01-CH'),
    (67, '31ª-Fev-25', 'C031-2025-02-CH'),
    (42, '32ª-Mar-25', 'C032-2025-03-CH'),
    (68, '33ª-Abr-25', 'C033-2025-04-SC'),
    (69, '34ª-Mai-25', 'C034-2025-05-SC'),
    (45, '35ª-Jun-25', 'C035-2025-06-SC'),
    (46, '36ª-Jul-25', 'C036-2025-07-SC'),
    (47, '37ª-Ago-25', 'C037-2025-08-SC'),
    (48, '38ª-Set-25', 'C038-2025-09-SC'),
    (111, '39ª-Out-25', 'C039-2025-10-CH'),
    (112, '40ª-Nov-25', 'C040-2025-11-CH'),
    (113, '41ª-Dez-25', 'C041-2025-12-CH'),
    (116, '42ª-Jan-26', 'C042-2026-01-CH'),
    (117, '43ª-Fev-26', 'C043-2026-02-CH'),
    (495, '44ª-Mar-26', 'C044-2026-03-CH'),
    (496, '45ª-Abr-26', 'C045-2026-04-SC'),
    (497, '46ª-Mai-26', 'C046-2026-05-SC'),
    (677, '47ª-Jun-26', 'C047-2026-06-SC')
)
SELECT
  'campanhas' AS tabela,
  COUNT(*) AS linhas_afetadas
FROM public.campanhas c
JOIN mapa m ON m.id_campanha = c.id_campanha
WHERE c.nome_campanha = m.nome_atual
UNION ALL
SELECT
  'biota_analise_consolidada' AS tabela,
  COUNT(*) AS linhas_afetadas
FROM public.biota_analise_consolidada b
JOIN mapa m ON m.nome_atual = b.nome_campanha
WHERE b.codigo_interno_opyta = 'BRAAVG002' OR b.id_projeto = 9
UNION ALL
SELECT
  'fisico_analise_consolidada' AS tabela,
  COUNT(*) AS linhas_afetadas
FROM public.fisico_analise_consolidada f
JOIN mapa m ON m.nome_atual = f.nome_campanha
WHERE f.codigo_interno_opyta = 'BRAAVG002';

-- Aplicacao, se aprovada:
-- 1) criar backups de public.campanhas, public.biota_analise_consolidada para BRAAVG002
--    e public.fisico_analise_consolidada para BRAAVG002 quando houver linhas;
-- 2) atualizar campanhas por id_campanha;
-- 3) atualizar campos denormalizados nome_campanha nas tabelas consolidadas;
-- 4) reexecutar auditoria de totais e produtos dependentes.
