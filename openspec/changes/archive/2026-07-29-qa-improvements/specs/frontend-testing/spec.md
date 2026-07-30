# Delta para frontend-testing

## ADDED Requirements

### R-FT01: Vitest con React Testing Library

El sistema DEBE incluir `vitest`, `@testing-library/react`, `@testing-library/jest-dom` y `jsdom` como dependencias de desarrollo en `frontend/package.json`. El archivo `frontend/vite.config.ts` DEBE configurar el entorno de test con `test.environment: 'jsdom'` y `globals: true`. El script `test` en `package.json` DEBE ejecutar `vitest run`.

#### Escenario: Vitest configurado correctamente

- DADO que las dependencias están instaladas
- CUANDO se ejecuta `npx vitest run` en `frontend/`
- ENTONCES vitest DEBE iniciar sin errores de configuración
- Y DEBE usar `jsdom` como entorno

#### Escenario: Test de componente renderiza

- DADO que existe `frontend/src/App.test.tsx` con un test que renderiza `<App />`
- CUANDO se ejecuta `npx vitest run`
- ENTONCES el test DEBE pasar
- Y DEBE verificar que el componente se renderiza sin errores

### R-FT02: Code-splitting con manualChunks

El sistema DEBE configurar `build.rollupOptions.output.manualChunks` en `frontend/vite.config.ts` para separar: `react` (react, react-dom), `antd` (antd, @ant-design/icons), y `app` (código propio de la aplicación). El build DEBE producir al menos tres archivos JS separados correspondientes a estos grupos.

#### Escenario: Build produce chunks separados

- DADO que `vite.config.ts` tiene `manualChunks` configurado
- CUANDO se ejecuta `npm run build` en `frontend/`
- ENTONCES `frontend/dist/assets/` DEBE contener archivos JS separados para react, antd y app
- Y el build DEBE completar con código 0

#### Escenario: Chunks tienen nombres predecibles

- DADO la configuración de `manualChunks`
- CUANDO se inspecciona el output del build
- ENTONCES los nombres de chunk DEBEN seguir un patrón predecible (ej: `react-*.js`, `antd-*.js`, `app-*.js`)
- Y NO DEBE haber un solo bundle que contenga todo el código
