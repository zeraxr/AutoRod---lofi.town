# Notas sobre Inyección Nivel Kernel (Ring 0)

Para evitar la bandera `LLMHF_INJECTED` de Windows, AutoRod prepara el terreno para el uso de drivers Ring 0.

## Interception API
1. **Requisitos**: Instalar el driver original de Interception (requiere reinicio y privilegios de Administrador).
2. **Limitaciones**: Algunos sistemas antitrampas (como Vanguard o EasyAntiCheat) auditan la carga del driver `interception.sys`. Este componente existe para fiabilidad I/O, no para evasión directa de rootkits antitrampas.
3. **Mapeo**: El simulador debe traducir `KeyCode` a *Scan Codes* exactos de hardware (make/break codes), eludiendo el Ring 3 (Userland) por completo.