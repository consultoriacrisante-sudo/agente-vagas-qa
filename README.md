# Agente Vagas QA

Agente pessoal para descoberta, validação, ranking e entrega de vagas compatíveis com o perfil profissional do candidato.

## Regras de produto

- Somente vagas **100% remotas**. Híbrido e presencial são eliminatórios.
- Trilha principal: **QA / Quality Engineering / Test Automation / SDET / Mobile QA**.
- Trilha de transição: **Salesforce Junior / Entry Level / Associate / Trainee**.
- Identificar **CLT / PJ** somente quando houver evidência na publicação; caso contrário, `Não informado`.
- Não tratar Match Score como probabilidade de contratação.
- Não repetir vagas já processadas/enviadas.
- Preferir a URL da vaga original/ATS à URL de agregadores.
- Em caso de conflito sobre modalidade remota, rejeitar a vaga.

## Arquitetura

```text
Fontes públicas / ATS / pesquisa web
              ↓
        collectors/
              ↓
       normalização
              ↓
     Remote Gate (hard)
              ↓
       classificação
       QA | Salesforce
              ↓
        Match Score
              ↓
       deduplicação
              ↓
          Supabase
              ↓
          Telegram
              ↑
       Flask / Vercel
              ↑
          Cron diário
```

## Fontes priorizadas

A estratégia é usar integrações públicas/documentadas de ATS quando possível, começando por Greenhouse, Lever, Ashby e SmartRecruiters, além de descoberta via pesquisa para localizar páginas originais de vagas. Agregadores podem participar da descoberta, mas a vaga original é a referência preferida.

## Segurança

Segredos nunca devem ser commitados. Use variáveis de ambiente e `.env` apenas localmente. Veja `.env.example`.

## Estado

MVP em construção.
