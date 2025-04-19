
# INTEGRANTES

- **ALARCON GOMEZ BILY ALEXIS**
- **ESPIRITU VILLAR TEVIS**
- **HORNA CERNA DAYANA ESTEFANY**
- **HURTADO MILIAN JEAN HARLEY**
- **DURAND PALACIOS ABIGAIL**

---

# Documentación del Generador de CRUD para Laravel

Esta aplicación en Python está diseñada para automatizar la generación de operaciones CRUD (Crear, Leer, Actualizar, Eliminar) en proyectos Laravel.  
Permite a los usuarios introducir definiciones de esquemas SQL y genera archivos correspondientes de modelo, migración, controlador y vistas en Laravel, así como definiciones de rutas.  
Adicionalmente, ofrece una interfaz gráfica de usuario (GUI) para una interacción más sencilla.

---

## 🧩 Características

- Análisis de sentencias SQL `CREATE TABLE` para extraer la estructura de la tabla.
- Generación de archivos de modelo Laravel basados en el esquema SQL.
- Creación de archivos de migración Laravel con definiciones de esquema.
- Generación de archivos de controlador Laravel con operaciones CRUD.
- Creación de archivos de vista Blade Laravel para operaciones de registro, listado y edición.
- Generación automática de rutas web para las operaciones CRUD.
- GUI para una interacción fácil y operativa.

---

## 🔧 Requisitos

- Python 3.x  
- Biblioteca Tkinter para la GUI.  
- Conocimientos básicos de SQL y el framework Laravel.

---

## 🖥️ Descripción de la Interfaz Gráfica

### Componentes Principales:

- **Área de Sentencia SQL**: Campo de texto para ingresar tu sentencia `CREATE TABLE`.
- **Botón Procesar SQL**: Extrae los detalles de la tabla.
- **Visualización de Campos**: Muestra campos con posibilidad de editar propiedades:
  - `Primary Key`
  - `Nullable`
  - `Mandatory`
- **Botones de Generación**: Generan los archivos Laravel necesarios:
  - Modelo
  - Migración
  - Controlador
  - Vistas Blade
  - Rutas web

---

## 🚀 Ejemplo de Uso

### 1. Iniciar la Aplicación

Ejecuta el script en Python. Aparecerá la GUI.

### 2. Introducir Sentencia SQL

Ejemplo de tabla **CLIENTE**:

```sql
CREATE TABLE CLIENTE (
  NRODOCUMENTO Varchar(12) NOT NULL,
  TIPODOCUMENTO Varchar(2),
  LINK Varchar(36),
  RAZONNOMBRE Varchar(255),
  DIASCREDITO Smallint,
  LIMITECREDITO Numeric(16,6),
  EMAIL Varchar(64),
  TELEFONO Varchar(48),
  CONTACTO Varchar(64),
  CLAVEWEB Varchar(16),
  TIPOCLIENTE Varchar(64),
  TIPOORIGEN Smallint,
  FECHANACIMIENTO Date,
  OCUPACION Varchar(128),
  DIRECCION Varchar(250),
  REFERENCIA Varchar(250),
  DNIFAMILIAR Varchar(12),
  TELEFONOCONTACTO Varchar(16),
  FECULTIMACOMPRA Date,
  DOCULTIMACOMPRA Varchar(18),
  PORCENTAJE_DESCUENTO Numeric(16,2),
  PORCENTAJE_MORA Numeric(16,2),
  PRIMARY KEY (NRODOCUMENTO)
);
```

Ejemplo de tabla **PROVEEDOR**:

```sql
CREATE TABLE PROVEEDOR (
  RUC Varchar(12) NOT NULL,
  RAZONSOCIAL Varchar(256),
  DIASCREDITO Integer,
  CODCUENTA Varchar(18),
  LIMITECREDITO Numeric(16,6),
  CUENTABANCARIA Varchar(64),
  SERIE Varchar(6),
  DIRECCION Varchar(128),
  EMAIL Varchar(36),
  TELEFONO Varchar(16),
  CONTACTO Varchar(64),
  FECHA Date,
  PRIMARY KEY (RUC)
);
```

### 3. Procesar SQL

Presiona **"Procesar SQL"** para ver los campos.  
Podrás editar propiedades de los campos (`nullable`, `mandatory`, etc.).

### 4. Generar Archivos

- **Vistas Blade (`listar.blade.php`)**: solo se muestran los campos `mandatory`.
- **Controlador Laravel**: usa los `mandatory` en las validaciones.
- **Modelo Laravel**: creado a partir del esquema.
- **Migración Laravel**: genera el archivo con el esquema.
- **Rutas Web**: crea rutas `resource`.

---

## ⚙️ Funciones Adicionales

- **Excepciones Personalizadas**:  
  - `SQLParsingError` para errores de análisis SQL.
- **Pluralización y Tipos HTML**:  
  - Pluraliza nombres en español.  
  - Convierte tipos SQL a tipos de entrada HTML.
- **Generación y Guardado de Archivos**:  
  - Se guardan en el directorio seleccionado por el usuario.

---
