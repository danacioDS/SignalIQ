# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can’t go back!**

If you aren’t satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you’re on your own.

You don’t have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn’t feel obligated to use this feature. However we understand that this tool wouldn’t be useful if you couldn’t customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).


#### Deploy 

## 🚀 **CÓDIGO PARA DESPLEGAR**

---

## 📋 **PASO 1: SUBIR CAMBIOS A GITHUB**

```bash
cd ~/repo_lab/SignalIQ

# Verificar estado
git status

# Agregar todos los cambios
git add .

# Commit con mensaje
git commit -m "feat: nuevo dashboard sin hardcode, arquitectura mejorada y secciones académicas"

# Subir a GitHub
git push origin main
```

---

## 📋 **PASO 2: DESPLEGAR FRONTEND EN VERCEL**

```bash
cd ~/repo_lab/SignalIQ/frontend

# 1. Instalar dependencias (si es necesario)
npm install

# 2. Build de producción
npm run build

# 3. Desplegar a Vercel
CI=false vercel --prod --force
```

### Cuando Vercel te pregunte:

```text
? Which team? → Daniel Canedo's projects
? Link to existing project? → yes
? Which project? → signaliq
? Would you like to pull environment variables now? → no
```

---

## 📋 **PASO 3: DESPLEGAR BACKEND EN RENDER**

**Desde el Dashboard de Render:**

1. **Ve a:** https://dashboard.render.com
2. **Selecciona el servicio** `signaliq-api`
3. **Ve a:** Manual Deploy → **"Deploy latest commit"**
4. **Espera a que termine** (2-3 minutos)

**O desde la terminal (si tienes CLI de Render):**

```bash
# Si no tienes el CLI, instalar:
npm install -g render-cli

# Luego:
render deploy --service signaliq-api
```

---

## 📋 **PASO 4: VERIFICAR DEPLOY**

```bash
# 1. Verificar frontend
curl -I https://signaliq-zeta.vercel.app

# 2. Verificar backend
curl https://signaliq-api.onrender.com/api/health

# 3. Probar señales en vivo
curl https://signaliq-api.onrender.com/api/signals-live?tickers=NVDA,AAPL,MSFT

# 4. Probar precios
curl https://signaliq-api.onrender.com/api/prices/NVDA
```

---

## 📋 **COMANDO ÚNICO (COPY-PASTE)**

Si quieres hacer todo de una vez:

```bash
cd ~/repo_lab/SignalIQ && \
git add . && \
git commit -m "feat: nuevo dashboard sin hardcode, arquitectura mejorada" && \
git push origin main && \
cd frontend && \
npm run build && \
CI=false vercel --prod --force
```

---

## ✅ **URLS DE PRODUCCIÓN**

| Componente | URL |
|------------|-----|
| **Frontend** | `https://signaliq-zeta.vercel.app` |
| **Backend** | `https://signaliq-api.onrender.com` |
| **GitHub** | `https://github.com/danacioDS/SignalIQ` |

---

## 🔧 **SI EL DEPLOY FALLA**

### Frontend (Vercel):
```bash
# Ver el error
npm run build 2>&1 | tail -50

# Si es problema de dependencias:
rm -rf node_modules package-lock.json
npm install
npm run build
CI=false vercel --prod --force
```

### Backend (Render):
- **Ve a los logs** en Render Dashboard
- **Busca el error** y pégamelo aquí
- **O reinicia el servicio** desde Render Dashboard

---

**¿Ya ejecutaste el deploy?** 🚀
