# 📤 GITHUB + VERCEL DEPLOYMENT SETUP

**Status:** ✅ Repositorio local preparado  
**Commit:** 60573be - Initial commit  
**Fecha:** 2026-05-02

---

## 🚀 PASOS A SEGUIR (TODO MANUAL)

Tu repositorio local está completamente configurado y listo. Ahora necesitas:

### PASO 1️⃣ CREAR REPOSITORIO EN GITHUB

#### 1.1 Ir a GitHub

```
Abre: https://github.com/new
```

#### 1.2 Llenar el formulario

| Campo | Valor |
|-------|-------|
| Repository name | `pixartek` |
| Description | `Robot Educativo de Pintura Artística` |
| Visibility | **Public** (recomendado para Vercel) |
| Add .gitignore | **NO** (ya lo tenemos) |
| Add license | **NO** (ya lo tenemos) |

#### 1.3 Crear repositorio

Haz clic en **"Create repository"**

### PASO 2️⃣ CONECTAR TU REPOSITORIO LOCAL A GITHUB

Después de crear el repo en GitHub, te mostrará una pantalla con comandos. **COPIA Y EJECUTA ESTO EN TU TERMINAL:**

#### Si es tu PRIMER push:

```bash
# Navega a tu proyecto
cd C:\Users\Jochy\OneDrive\Desktop\pixartek

# Cambia el nombre de rama a 'main'
git branch -M main

# Añade el remote de GitHub
git remote add origin https://github.com/TU_USUARIO/pixartek.git

# Sube el código
git push -u origin main
```

**Reemplaza `TU_USUARIO` con tu usuario de GitHub**

#### Si ya tiene origin configurado:

```bash
cd C:\Users\Jochy\OneDrive\Desktop\pixartek

# Actualiza origin
git remote set-url origin https://github.com/TU_USUARIO/pixartek.git

# Sube
git push -u origin main
```

### ⏳ Espera a que termine (puede tomar 2-3 minutos)

Deberías ver:
```
Counting objects: 100% (93/93), done.
Writing objects: 100% (93/93), ...
...
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

## PASO 3️⃣ CONFIGURAR VERCEL PARA DEPLOY

### 3.1 Crear cuenta en Vercel

1. Ve a **https://vercel.com/signup**
2. Selecciona **"Continue with GitHub"**
3. Autoriza a Vercel
4. Completa tu perfil si es necesario

### 3.2 Importar proyecto en Vercel

1. En el dashboard de Vercel, haz clic en **"Add New"**
2. Selecciona **"Project"**
3. Haz clic en **"Import Git Repository"**

### 3.3 Buscar y seleccionar tu repo

1. Busca `pixartek` en el campo de búsqueda
2. Haz clic en tu repositorio
3. Haz clic en **"Import"**

### 3.4 Configurar proyecto

En la pantalla de configuración:

**Framework Preset:**
```
Next.js
```

**Root Directory:**
```
frontend
```

**Build Command:**
```
npm run build
```

**Output Directory:**
```
.next
```

### 3.5 Environment Variables (OPCIONAL)

Si tu frontend necesita conectarse al backend, añade:

1. Haz clic en **"Environment Variables"**
2. Añade:
   - **Name:** `NEXT_PUBLIC_API_URL`
   - **Value:** `https://tu-backend.com` (si tienes)

### 3.6 Deploy

1. Haz clic en **"Deploy"**
2. ⏳ Espera 3-5 minutos
3. Vercel te dará una URL como:
   ```
   https://pixartek.vercel.app
   ```

---

## ✅ VERIFICACIÓN

Después de completar los pasos, verifica:

### En GitHub
```bash
# Ver remote
git remote -v

# Ver branches
git branch -a
```

Deberías ver:
```
origin  https://github.com/TU_USUARIO/pixartek.git (fetch)
origin  https://github.com/TU_USUARIO/pixartek.git (push)

* main
  remotes/origin/main
```

### En Vercel
1. Accede a tu URL de Vercel
2. Deberías ver la página de PIXARTEK cargando
3. Verifica que los componentes funcionan

---

## 🔄 WORKFLOW FUTURO

Cada vez que hagas cambios:

```bash
# 1. Haz cambios en tu código
# 2. Staged cambios
git add .

# 3. Commit
git commit -m "Descripción de cambios"

# 4. Push a GitHub
git push origin main
```

**Vercel automáticamente:**
- ✅ Detecta el push
- ✅ Inicia el build
- ✅ Despliega la nueva versión
- ✅ Te notifica cuando esté listo

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### Error: "fatal: not a git repository"
```bash
# Navega a la carpeta correcta
cd C:\Users\Jochy\OneDrive\Desktop\pixartek
```

### Error: "fatal: remote origin already exists"
```bash
# Reemplaza el origin
git remote set-url origin https://github.com/TU_USUARIO/pixartek.git
```

### Error: "Authentication failed"
GitHub ya no acepta passwords. Tienes dos opciones:

**Opción A: Token Personal (Recomendado)**
1. Ve a https://github.com/settings/tokens
2. Haz clic en "Generate new token"
3. Genera un token con permisos `repo`
4. Usa el token en lugar de tu password

**Opción B: SSH Key**
1. Genera SSH key: `ssh-keygen -t ed25519 -C "tu.email@gmail.com"`
2. Añade a GitHub: https://github.com/settings/keys
3. Usa URL SSH: `git@github.com:TU_USUARIO/pixartek.git`

### Vercel no muestra cambios
1. Espera 5 minutos
2. En Vercel dashboard, haz clic en **"Deployments"**
3. Haz clic en **"Redeploy"** si es necesario

---

## 📊 CHECKLIST FINAL

- [ ] Creé repositorio en GitHub
- [ ] Ejecuté `git remote add origin ...`
- [ ] Ejecuté `git push -u origin main`
- [ ] Creé cuenta en Vercel
- [ ] Importé proyecto en Vercel
- [ ] Configuré root directory a `frontend`
- [ ] Deploy completó exitosamente
- [ ] Accedí a la URL de Vercel
- [ ] Página carga correctamente

---

## 🎉 ¡FELICIDADES!

Una vez completados estos pasos:

✅ Tu código está en GitHub  
✅ Tu frontend se despliega automáticamente en Vercel  
✅ Cualquier push actualiza el deployment  
✅ Tienes una URL pública para compartir

**URL Final:**
```
https://pixartek.vercel.app
```

---

## 💡 SIGUIENTES PASOS

1. **Backend:** Desplegar en Heroku, Railway o tu propio servidor
2. **Vision Nodes:** Mantener corriendo en RPis locales
3. **Custom Domain:** Compra dominio y conecta a Vercel
4. **CI/CD:** Configura GitHub Actions para tests automáticos

---

**¿Preguntas?** Abre un issue en GitHub o contacta directamente.

**Última actualización:** 2026-05-02
