"""
🩹 CORREÇÃO (PATCH) PARA UM BUG DA BIBLIOTECA discord.py-self
==============================================================

POR QUE ESTE ARQUIVO EXISTE?
----------------------------
O erro "'NoneType' object is not iterable" que aparecia ao ligar o bot
NÃO era culpa do nosso código. Ele acontecia DENTRO da biblioteca
`discord.py-self`, no arquivo `state.py`, na função `parse_ready_supplemental`.

O que acontece é o seguinte:
1. O bot conecta no Discord normalmente. ✅
2. O Discord envia um pacote de dados de "boas-vindas" (READY_SUPPLEMENTAL).
3. A biblioteca tenta LER campos desse pacote como se fossem listas, por exemplo:
       for p in data.get('pending_payments', [])
4. PORÉM, o Discord às vezes envia esses campos como `null` (None) em vez de
   uma lista vazia `[]`. E o `.get('campo', [])` do Python retorna `None`
   (e não o `[]`) quando a chave EXISTE mas o valor é `None`.
5. Aí o Python tenta fazer "for p in None" e estoura o erro:
       TypeError: 'NoneType' object is not iterable 💥

A SOLUÇÃO (este arquivo):
-------------------------
Nós "interceptamos" (monkey-patch) a função problemática da biblioteca e,
ANTES de ela rodar, trocamos todos os campos que vieram como `None` por
listas/dicionários vazios. Assim a biblioteca nunca mais quebra. 🛡️

Esse patch funciona mesmo quando a biblioteca é reinstalada do zero
(como acontece na Square Cloud), porque ele é aplicado em tempo de execução,
direto no nosso código.
"""

import logging

logger = logging.getLogger("DiscordPatch")

# Controle para garantir que o patch seja aplicado UMA única vez
_patch_aplicado = False


def aplicar_patch_discord():
    """Aplica a correção no discord.py-self. Pode ser chamado várias vezes,
    mas só aplica de fato na primeira vez. ✅"""
    global _patch_aplicado
    if _patch_aplicado:
        return

    try:
        from discord.state import ConnectionState
    except Exception as e:  # pragma: no cover
        print(f"⚠️ [PATCH] Não foi possível importar o ConnectionState do discord: {e}")
        return

    # Guardamos a função original para chamá-la depois
    _original = ConnectionState.parse_ready_supplemental

    # ----------------------------------------------------------------
    # Campos que a biblioteca tenta percorrer como LISTAS.
    # Se vierem como None, trocamos por uma lista vazia [].
    # ----------------------------------------------------------------
    CAMPOS_LISTA_READY = [
        "users",
        "guilds",
        "merged_members",
        "relationships",
        "private_channels",
        "connected_accounts",
        "pending_payments",   # 👈 este era o que estava quebrando o bot!
        "read_state",
        "friend_suggestion_count",
    ]
    CAMPOS_LISTA_EXTRA = [
        "guilds",
        "merged_members",
        "lazy_private_channels",
    ]

    def _sanitizar(dicionario, campos_lista):
        """Troca valores None por [] nos campos que precisam ser listas."""
        if not isinstance(dicionario, dict):
            return
        for campo in campos_lista:
            if campo in dicionario and dicionario[campo] is None:
                print(f"🩹 [PATCH] Campo '{campo}' veio como None — trocando por lista vazia [].")
                dicionario[campo] = []

    def parse_ready_supplemental_seguro(self, extra_data):
        """Versão segura: limpa os dados antes de deixar a biblioteca processá-los."""
        try:
            # 1) Limpa os dados principais (que ficam guardados em self._ready_data)
            data = getattr(self, "_ready_data", None)
            _sanitizar(data, CAMPOS_LISTA_READY)

            # Caso especial: user_guild_settings deve ser um dicionário com "entries"
            if isinstance(data, dict):
                ugs = data.get("user_guild_settings")
                if ugs is None:
                    data["user_guild_settings"] = {"entries": []}
                elif isinstance(ugs, dict) and ugs.get("entries") is None:
                    ugs["entries"] = []

            # 2) Limpa os dados extras recebidos no evento
            _sanitizar(extra_data, CAMPOS_LISTA_EXTRA)

            # Caso especial: merged_presences deve ser um dicionário
            if isinstance(extra_data, dict):
                mp = extra_data.get("merged_presences")
                if mp is None:
                    extra_data["merged_presences"] = {"guilds": [], "friends": []}
                elif isinstance(mp, dict):
                    if mp.get("guilds") is None:
                        mp["guilds"] = []
                    if mp.get("friends") is None:
                        mp["friends"] = []
        except Exception as e:
            # Se algo der errado na limpeza, apenas avisamos e seguimos
            print(f"⚠️ [PATCH] Erro ao limpar dados (seguindo mesmo assim): {e}")

        # 3) Agora sim chamamos a função original da biblioteca, já com dados limpos
        return _original(self, extra_data)

    # Substituímos a função da biblioteca pela nossa versão segura
    ConnectionState.parse_ready_supplemental = parse_ready_supplemental_seguro

    _patch_aplicado = True
    print("✅ [PATCH] Correção do discord.py-self aplicada com sucesso! (bug do NoneType resolvido)")
    logger.info("Patch do discord.py-self aplicado (parse_ready_supplemental seguro).")
