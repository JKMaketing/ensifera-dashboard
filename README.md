# Ensífera · Tablero de Impacto en Ventas

Tablero interactivo y autocontenido (un solo archivo `index.html`, sin dependencias externas) que lee los resultados publicitarios de **Ensífera** — aviturismo y guías de aves — y su impacto en ventas.

## Qué muestra

- **Rango de fechas flexible**: presets (Todo, Junio, Julio, periodo Ensifera COP, últimos 7 días) y rango personalizado desde/hasta.
- **Comparación de periodos**: cada KPI contra el periodo anterior de igual duración, con variación coloreada.
- **KPIs**: ventas totales, inversión publicitaria, ROAS, conversaciones, costo por conversación e impresiones.
- **Serie diaria**: ventas, inversión y ROAS día a día (una sola escala por gráfico).
- **Campañas** (datos reales de Meta Ads): inversión, impresiones, clics y CPC por campaña.
- **Sedes**: distribución de conversaciones por sede (Cali, Medellín, Bogotá).
- **Productos**: ranking de productos más consultados.
- **Verificación Hoja ↔ Meta Ads**: reconciliación de la inversión anotada en la hoja contra la cuenta real.

## Fuentes de datos

- Hoja **«Conglomerado Gastos Publicitarios 2026.xlsx»** (incluida en este repo).
- Cuenta **Meta Ads «Ensifera COP»** (ID `1580457616921076`, moneda COP), con detalle diario desde el 15 jul 2026.

Los datos están embebidos en el HTML como una instantánea (JSON) al momento de generar el tablero. Para actualizarlos se regenera desde la hoja y la cuenta de Meta Ads.

## Notas metodológicas

- **ROAS** = ventas ÷ inversión publicitaria.
- **Migración de cuenta**: hasta el 15 jul 2026 la pauta corría en una cuenta en **USD** (convertida a COP × 3.600); desde el 16 jul migró a **Ensifera COP**. El tablero unifica ambos periodos en una sola serie.
- Rango de datos actual: **23 jun 2026 → 29 jul 2026**.

## Uso

Abre `index.html` en cualquier navegador, o publícalo con **GitHub Pages** (Settings → Pages → Deploy from branch → root) para una URL compartible.

---

Generado para Ensífera · **JK Marketing** (contacto@juankno.com)
