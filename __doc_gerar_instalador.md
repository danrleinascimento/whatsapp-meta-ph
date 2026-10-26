1. Preparar na PH (uma vez por versão)

Recompilar o PH.bpl e o GEPH no C++ Builder 5. Sem isso, o GEPH não encontra o serviço novo.

Em C:\projetos\python\whatsmeta, gerar o exe e o instalador:

.\scripts\build_exe.ps1
.\scripts\build_instalador.ps1

O arquivo para levar ao cliente é instalador\saida\instalarWHATSPH.exe. Ele já contém o whatsph.exe e o script de preparação.
