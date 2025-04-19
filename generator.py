import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import re
import os
import datetime
import inflect
import random


class SQLParsingError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


# Definición de las constantes para las casillas de verificación
CHECKBOX_TICKED = "☑"
CHECKBOX_UNTICKED = "☐"


def pluralizar(palabra):
    if palabra.endswith(('a', 'e', 'i', 'o', 'u')):
        return palabra + 's'
    elif palabra.endswith('z'):
        return palabra[:-1] + 'ces'
    elif palabra.endswith('ión'):
        return palabra[:-3] + 'iones'
    elif palabra.endswith(('r', 'l', 'n', 'd')):
        return palabra + 'es'
    else:
        return palabra + 'es'


def parse_sql_table(sql):
    if not sql.strip():  # Verificar si el SQL está vacío
        raise SQLParsingError("Rellene el sql porfavor")

    table_pattern = re.compile(r"CREATE TABLE (\w+)", re.IGNORECASE)
    table_match = table_pattern.search(sql)
    if not table_match:  # Verificar si se encuentra el nombre de la tabla
        raise SQLParsingError("Table name not found")

    table_name = table_match.group(1)

    field_pattern = re.compile(
        r"(\w+)\s+(\w+)(\(\d+(,\d+)?\))?\s*(NOT NULL)?", re.IGNORECASE)
    pk_pattern = re.compile(r"PRIMARY KEY\s*\((.*?)\)", re.IGNORECASE)

    fields = []
    for match in field_pattern.finditer(sql):
        if match.group(2).upper() in ["TABLE", "KEY"]:
            continue
        fields.append({
            "name": match.group(1),
            "type": match.group(2),
            "size": match.group(3).strip("()") if match.group(3) else "",
            "nullable": not bool(match.group(5)),
            "primary_key": False,
            "mandatory": True  # Inicialmente, todos los campos son obligatorios
        })

    pk_match = pk_pattern.search(sql)
    if pk_match:
        pk_fields = {pk_field.strip()
                     for pk_field in pk_match.group(1).split(",")}
        for field in fields:
            if field["name"] in pk_fields:
                field["primary_key"] = True

    return table_name, fields


def sql_to_html_input_type(sql_type):

    mapping = {
        'varchar': 'text',
        'int': 'number',
        'bigint': 'number',
        'float': 'number',
        'double': 'number',
        'decimal': 'number',
        'date': 'date',
        'datetime': 'datetime-local',
        'timestamp': 'datetime-local',
        'boolean': 'checkbox',  # Este requerirá lógica especial si se usa
    }
    return mapping.get(sql_type.lower(), 'text')


def generar_fields_html(fields, valores_actuales=None, editable=True):
    html = ""
    for i in range(0, len(fields), 2):  # Iterar a través de los campos dos a dos
        html += '<div class="row">\n'
        for j in range(2):  # Dentro de cada fila, crear hasta dos columnas
            if i + j < len(fields):
                field = fields[i + j]
                # Asegurar que el nombre del campo esté en mayúsculas para la generación del HTML
                field_name_upper = field['name'].upper()
                field_label = field.get("label", field_name_upper).capitalize()
                html_input_type = sql_to_html_input_type(field["type"])
                # Asegurar que se usen nombres de propiedades en mayúsculas para los valores actuales
                current_value = valores_actuales.get(
                    field_name_upper, "") if valores_actuales else ""
                disabled_attr = " disabled" if not editable else ""

                # Construir el atributo 'value' utilizando la sintaxis de Blade y el nombre de la tabla en minúscula
                value_attr = f' value="{{{{ ${valores_actuales.get("object_name", "objeto").lower()}->{field["name"]} }}}}"' if current_value else ""

                # Insertar el atributo 'value' entre 'disable-feedback' y 'type'
                html += f'    <x-adminlte-input name="{field_name_upper}" label="{field_label}" placeholder="{field_label}" fgroup-class="col-md-6" disable-feedback{value_attr} type="{html_input_type}"{disabled_attr} />\n'
        html += '</div>\n'
    return html


def generar_vista_registrar(fields, table_name):
    fields_html = generar_fields_html(fields)
    return f"""@extends('adminlte::page')

@section('title', 'Registrar {table_name.capitalize()}')

@section('content_header')
    <h1 class="m-0 text-dark">Registrar {table_name.capitalize()}</h1>
@stop

@section('content')
@if ($errors->any())
    <div class="alert alert-danger">
        <strong>Error</strong> Hubo problemas con los datos ingresados<br><br>
        <ul>
            @foreach ($errors->all() as $error)
                <li>{{{{
{'$error'} }}}}</li>
            @endforeach
        </ul>
    </div>
@endif

@if(session('success'))
    <div class="alert alert-success mt-2">
        <strong>{{{{ Session::get('success') }}}}</strong>
    </div>
@endif

<form action="{{{{ route('{pluralizar(table_name)}.store') }}}}" method="POST" autocomplete="off">
    @csrf
{fields_html}

    <x-adminlte-button class="btn-flat" type="submit" label="Registrar" theme="success" icon="fas fa-lg fa-save"/>
</form>
@stop
"""


def generar_vista_listar(fields, table_name, mandatory_fields, primary_key):
    columnas = ''.join(
        [f"                <th>{field.get('label', field['name'].capitalize())}</th>\n" for field in fields if field['name'] in mandatory_fields])
    fields_data = ''.join(
        [f"                <td>{{{{ ${table_name}->{field['name']} }}}}</td>\n" for field in fields if field['name'] in mandatory_fields])
    table_name_plural = pluralizar(table_name)
    return f"""
@extends('adminlte::page')
@section('title', 'Listado de {table_name.capitalize()}')

@section('content_header')
    <h1 class="m-0 text-dark">Listado de {table_name_plural.capitalize()}</h1>
@stop

@section('content')
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">{table_name_plural.capitalize()} Registrados</h3>
        </div>
        <!-- /.card-header -->
        <div class="card-body">
            <table id="{table_name_plural}" class="table table-bordered table-striped">
                <thead>
                    <tr>
{columnas}                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    @foreach (${table_name_plural} as ${table_name})
                        <tr>
{fields_data}                            <td>
                                <<a href="{{{{ route('{table_name_plural}.edit', ['{table_name}' => ${table_name}->{primary_key}]) }}}}" class="btn btn-xs btn-primary">Editar</a>
                                <form action="{{{{ route('{table_name_plural}.destroy', ['{table_name}' => ${table_name}->{primary_key}]) }}}}" method="POST" style="display: inline-block;">
                                    @csrf
                                    @method('DELETE')
                                    <button type="submit" class="btn btn-xs btn-danger">Eliminar</button>
                                </form>
                            </td>
                        </tr>
                    @endforeach
                </tbody>
            </table>
        </div>
        <!-- /.card-body -->
    </div>
    <!-- /.card -->
    <div>
       {{{{ ${table_name_plural}->links() }}}}
    </div>
@stop
"""


def generar_vista_editar(fields, table_name, primary_key):
    # Asegurar que los nombres de las variables en `valores_actuales` estén en mayúsculas
    valores_actuales = {field['name'].upper(
    ): f"{{${{table_name.lower()}}->{field['name']}}}" for field in fields}

    # Usar el nombre del objeto en minúsculas para mantener consistencia con la instancia del modelo
    valores_actuales["object_name"] = table_name.lower()
    fields_html = generar_fields_html(fields, valores_actuales, editable=False)
    table_name_plural = pluralizar(table_name)
    return f"""@extends('adminlte::page')

@section('title', 'Editar {table_name.capitalize()}')

@section('content_header')
    <h1 class="m-0 text-dark">Editar {table_name.capitalize()}</h1>
@stop

@section('content')
@if ($errors->any())
    <div class="alert alert-danger">
        <strong>Error</strong> Hubo problemas con los datos ingresados<br><br>
        <ul>
            @foreach ($errors->all() as $error)
                <li>{{{{ $error }}}}</li>
            @endforeach
        </ul>
    </div>
@endif

@if(session('success'))
    <div class="alert alert-success mt-2">
        <strong>{{{{ session('success') }}}}</strong>
    </div>
@endif

<form action="{{{{ route('{table_name_plural}.update', ['{table_name}' => ${table_name}->{primary_key}]) }}}}" method="POST" autocomplete="off">
    @csrf
    @method('PUT')
{fields_html}

    <x-adminlte-button class="btn-flat" type="submit" label="Actualizar" theme="success" icon="fas fa-lg fa-save"/>
</form>
@stop
"""


def guardar_vista(table_name, contenido, nombre_archivo):
    nombre_carpeta_plural = pluralizar(table_name)
    # Ajusta la ruta base según necesites
    ruta_carpeta = os.path.join(nombre_carpeta_plural)

    # Crear la carpeta si no existe
    if not os.path.exists(ruta_carpeta):
        os.makedirs(ruta_carpeta)

    ruta_archivo = os.path.join(ruta_carpeta, nombre_archivo)
    with open(ruta_archivo, 'w') as archivo:
        archivo.write(contenido)
    print(f"Archivo {nombre_archivo} guardado en {ruta_carpeta}/")


def generar_y_guardar_vistas(table_name, fields):
    # Identificar los campos marcados como obligatorios
    mandatory_fields = [field['name']
                        for field in fields if field.get('mandatory', False)]

    # Identificar la clave primaria
    primary_key = next(
        (field['name'] for field in fields if field.get('primary_key', False)), 'id')

    # Generar contenido de las vistas
    contenido_registrar = generar_vista_registrar(fields, table_name)
    contenido_listar = generar_vista_listar(
        fields, table_name, mandatory_fields, primary_key)
    contenido_editar = generar_vista_editar(fields, table_name, primary_key)

    # Guardar las vistas
    guardar_vista(table_name, contenido_registrar, "registrar.blade.php")
    guardar_vista(table_name, contenido_listar, "listar.blade.php")
    guardar_vista(table_name, contenido_editar, "editar.blade.php")


def request_directory_and_create_files(table_name, fields):
    # Solicitar al usuario que seleccione el directorio donde guardar los archivos
    root = tk.Tk()
    root.withdraw()  # No queremos una ventana de TK completa, solo el diálogo
    save_path = filedialog.askdirectory()  # Abre el diálogo para elegir carpeta
    if not save_path:  # Si el usuario cancela la selección
        messagebox.showerror("Error", "No folder selected.")
        return

    # Generar y guardar las vistas HTML para el CRUD
    generar_y_guardar_vistas(table_name, fields)

    messagebox.showinfo("Success", "CRUD files generated successfully.")


def sql_to_laravel_type(sql_type):
    type_mapping = {
        'varchar': 'string',
        'integer': 'integer',
        'smallint': 'smallInteger',
        'numeric': 'decimal',
        'date': 'date'
    }
    match = re.match(r"(\w+)(?:\((\d+)(?:,(\d+))?\))?",
                     sql_type, re.IGNORECASE)
    if match:
        sql_data_type, size, decimal_place = match.groups()
        laravel_type = type_mapping.get(sql_data_type.lower(), 'string')
        if laravel_type == 'decimal' and decimal_place:
            return laravel_type, size, decimal_place
        elif size:
            return laravel_type, size, None
        else:
            return laravel_type, None, None
    else:
        return 'string', None, None


def sql_to_laravel_type(sql_type):
    type_mapping = {
        # True indica que soporta especificación de tamaño
        'varchar': ('string', True),
        'integer': ('integer', False),
        'smallint': ('smallInteger', False),
        'numeric': ('numeric', True),
        'date': ('date', False)
    }
    match = re.match(r"(\w+)(?:\((\d+)(?:,(\d+))?\))?",
                     sql_type, re.IGNORECASE)
    if match:
        sql_data_type, size, decimal_places = match.groups()
        laravel_type, supports_size = type_mapping.get(
            sql_data_type.lower(), ('string', True))
        return laravel_type, size if supports_size else None, decimal_places
    else:
        return 'string', None, None


def generate_controller(table_name, fields, save_path):
    # Encontrar el nombre de la clave primaria
    primary_key = next(
        (field['name'] for field in fields if field.get('primary_key', False)), 'id')

    validation_rules = []
    for field in fields:
        # Determinar si el campo es obligatorio o no basado en 'mandatory'
        validation_type = 'required' if field.get(
            'mandatory', False) else 'nullable'
        size = field.get('size')
        laravel_type = 'string'  # Este ejemplo siempre usa string, ajusta según sea necesario
        rule = f"'{field['name']}' => '{validation_type}|{laravel_type}"
        if size:
            rule += f"|max:{size}"
        rule += "'"
        validation_rules.append(rule)

    validation_rules_str = ",\n        ".join(validation_rules)

    controller_content = f"""<?php

namespace App\Http\Controllers;

use App\Models\{table_name.capitalize()};
use Illuminate\Http\Request;

class {table_name.capitalize()}Controller extends Controller
{{
    public function index()
    {{
        ${table_name.lower()}s = {table_name.capitalize()}::orderBy('{primary_key}', 'asc')->paginate(6);
        return view('{table_name.lower()}s.listar', compact('{table_name.lower()}s'));
    }}

    public function create()
    {{
        return view('{table_name.lower()}s.registrar');
    }}

    public function store(Request $request)
    {{
        $request->validate([{validation_rules_str}]);

        {table_name.capitalize()}::create($request->all());

        return redirect()->route('{table_name.lower()}s.index')->with('success', '{table_name.capitalize()} creado con éxito.');
    }}

    public function show({table_name.capitalize()} ${table_name.lower()})
    {{
        // Implementación del método show
    }}

    public function edit({table_name.capitalize()} ${table_name.lower()})
    {{
        return view('{table_name.lower()}s.editar', compact('{table_name.lower()}'));
    }}

    public function update(Request $request, {table_name.capitalize()} ${table_name.lower()})
    {{
        $request->validate([{validation_rules_str}
        ]);

        ${table_name.lower()}->update($request->all());

        return redirect()->route('{table_name.lower()}s.index')->with('success', '{table_name.capitalize()} actualizado con éxito.');
    }}

    public function destroy({table_name.capitalize()} ${table_name.lower()})
    {{
        ${table_name.lower()}->delete();

        return redirect()->route('{table_name.lower()}s.index')->with('success', '{table_name.capitalize()} eliminado con éxito.');
    }}
}}
"""
    if not save_path.endswith('/'):
        save_path += '/'
    file_path = f"{save_path}{table_name.capitalize()}Controller.php"
    with open(file_path, 'w') as f:
        f.write(controller_content)
    return file_path  # Devuelve la ruta del archivo para mostrarla en el cuadro de diálogo


def create_controller(table_name, fields):
    if table_name and table_name != 'unknown':
        root = tk.Tk()
        root.withdraw()  # No queremos una ventana de TK completa, solo el diálogo
        save_path = filedialog.askdirectory()  # Abre el diálogo para elegir carpeta
        if save_path:  # Asegurarse de que el usuario no canceló el diálogo
            controller_path = generate_controller(
                table_name, fields, save_path)
            messagebox.showinfo(
                "Controller Generated", f"Controller file has been generated at: '{controller_path}'")
        else:
            messagebox.showerror("Error", "No folder selected.")
    else:
        messagebox.showerror(
            "Error", "No valid table name found. Please check your input.")


def generate_model(table_name, fields):
    # Inicializa la ventana de Tkinter
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal de Tkinter

    # Solicita al usuario que seleccione la ruta de guardado
    save_path = filedialog.askdirectory()

    if not save_path:  # Si el usuario cancela la selección
        messagebox.showerror("Error", "No folder selected.")
        return

    # Encuentra el campo clave primaria
    primary_key_field = next(
        (field for field in fields if field.get('primary_key', False)), None)
    primary_key = primary_key_field['name'] if primary_key_field else 'id'

    # Asegura que la clave primaria sea el primer elemento en `fillable` si no es 'id'
    fillable = []
    if primary_key != 'id':  # Si la clave primaria es algo distinto de 'id', agrégala primero
        fillable.append(f"'{primary_key}'")
    fillable += [f"'{field['name']}'" for field in fields if not field.get(
        'primary_key', False) and field['name'] != primary_key]

    # Genera el contenido del modelo
    model_content = f"""<?php

namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Factories\\HasFactory;
use Illuminate\\Database\\Eloquent\\Model;

class {table_name.capitalize()} extends Model
{{
    use HasFactory;

    
    protected $primaryKey = '{primary_key}';

    

    protected $fillable = [
        {', '.join(fillable)}
    ];
    public $timestamps = false;
    protected $guarded = [];
}}
"""

    # Guarda el modelo en el archivo especificado
    model_filename = f"{table_name.capitalize()}.php"
    model_path = os.path.join(save_path, model_filename)
    with open(model_path, 'w') as model_file:
        model_file.write(model_content)

    messagebox.showinfo(
        "Model Generated", f"Model '{model_filename}' has been generated successfully at '{save_path}'.")

    # Guardar el modelo en el archivo
    model_filename = f"{table_name.capitalize()}.php"
    model_path = os.path.join(save_path, model_filename)
    with open(model_path, 'w') as model_file:
        model_file.write(model_content)

    messagebox.showinfo(
        "Model Generated", f"Model '{model_filename}' has been generated successfully at '{save_path}'.")

    # Escribe el contenido en el archivo en la ruta seleccionada
    file_path = os.path.join(save_path, f'{table_name.capitalize()}.php')
    with open(file_path, 'w') as file:
        file.write(model_content)
    messagebox.showinfo("Model Generated",
                        f"Model file generated at: '{file_path}'")


def generate_migration_from_sql(sql_schema, save_path=None):
    lines = sql_schema.strip().split('\n')
    table_name_match = re.search(
        r"CREATE TABLE (\w+)", lines[0], re.IGNORECASE)
    if not table_name_match:
        print("No valid CREATE TABLE statement found.")
        return "", []
    table_name = table_name_match.group(1)

    primary_key = None  # Variable para almacenar el nombre del campo clave primaria
    fields = lines[1:-1]  # Todos los campos, excepto la primera y última línea
    migration_fields = ""

    # Buscar y establecer la clave primaria
    pk_pattern = re.compile(r"PRIMARY KEY\s*\((.*?)\)", re.IGNORECASE)
    pk_match = pk_pattern.search(sql_schema)
    if pk_match:
        primary_key = pk_match.group(1)

    for field in fields:
        field = field.strip().strip(',')
        # Saltar la definición de clave primaria
        if field.startswith("PRIMARY KEY"):
            continue

        field_parts = re.split(r"\s+", field, maxsplit=2)
        if len(field_parts) < 2:
            print(f"Skipping invalid field definition: {field}")
            continue  # No procesar líneas inválidas

        field_name, field_type = field_parts[:2]
        laravel_type, size, decimal_place = sql_to_laravel_type(field_type)

        field_definition = f"$table->{laravel_type}('{field_name}'"
        if size:
            field_definition += f", {size}"
            if decimal_place:
                field_definition += f", {decimal_place}"
        field_definition += ")"
        if 'NOT NULL' not in field:
            field_definition += "->nullable()"

        # Si el campo actual es la clave primaria, agregar ->primary()
        if field_name == primary_key:
            field_definition += "->primary()"

        migration_fields += f"{field_definition};\n"

    migration_content = f"""<?php

use Illuminate\\Support\\Facades\\Schema;
use Illuminate\\Database\\Schema\\Blueprint;
use Illuminate\\Database\\Migrations\\Migration;

class Create{pluralizar(table_name.capitalize())}Table extends Migration
{{
    public function up()
    {{
        Schema::create('{pluralizar(table_name.lower())}', function (Blueprint $table) {{
{migration_fields}            $table->timestamps();
        }});
    }}

    public function down()
    {{
        Schema::dropIfExists('{pluralizar(table_name.lower())}');
    }}
}}
"""
    return migration_content


def generate_migration_filename(table_name):
    # Obtener la fecha y hora actuales con el formato de Laravel para nombres de archivos de migración
    timestamp = datetime.datetime.now().strftime('%Y_%m_%d_')
    # Generar un ID aleatorio de seis dígitos
    random_id = f"{random.randint(100000, 999999):06d}"

    # Usar la función de pluralización personalizada para español
    plural_table_name = pluralizar(table_name.lower())

    return f"{timestamp}{random_id}_create_{plural_table_name}_table.php"


def generate_migration_only():
    save_path = filedialog.askdirectory()
    if save_path:
        sql_schema = sql_input_text.get("1.0", tk.END)
        # Aquí se corrige el desempaquetado para esperar solo un valor
        migration_content = generate_migration_from_sql(sql_schema)
        table_name = re.search(r"CREATE TABLE (\w+)",
                               sql_schema, re.IGNORECASE).group(1)
        migration_filename = generate_migration_filename(table_name)
        file_path = os.path.join(save_path, migration_filename)
        with open(file_path, 'w') as f:
            f.write(migration_content)
        messagebox.showinfo(
            "Migration Generated", f"Migration file has been generated at: '{file_path}'")


def write_to_file(filename, content, save_path):
    file_path = os.path.join(save_path, filename)
    with open(file_path, 'w') as file:
        file.write(content)
    messagebox.showinfo(
        "File Generated", f"File {filename} has been generated at: '{file_path}'")


def generate_routes():
    global table_name
    save_path = filedialog.askdirectory()
    if save_path and table_name:
        generate_routes_content(table_name, save_path)


def generate_routes_content(table_name, save_path):
    routes_content = f"""<?php

use App\Http\Controllers\{table_name.capitalize()}Controller;
use Illuminate\\Support\\Facades\\Route;

// routes\web.php (ruta para colocar el codigo solo copias y pega en el archivo)

Route::get('/', function () {{
    return view('welcome');
}});

Auth::routes();

Route::get('/home', [App\\Http\\Controllers\\HomeController::class, 'index'])->name('home');

Auth::routes();

Route::get('/home', function() {{
    return view('home');
}})->name('home')->middleware('auth');

Route::resource('/{pluralizar(table_name.lower())}', {table_name.capitalize()}Controller::class)->name('home','')->middleware('auth');
"""
    write_to_file('web.php', routes_content, save_path)


def toggle_value(item, index, values_list):
    item_list = list(item)
    current_value = item_list[index]
    item_list[index] = values_list[1] if current_value == values_list[0] else values_list[0]
    return item_list


def on_field_click(event):
    region = fields_table.identify_region(event.x, event.y)
    if region == 'cell':
        col = fields_table.identify_column(event.x)
        row_id = fields_table.identify_row(event.y)
        col_num = int(col.strip('#')) - 1
        if col_num in [3, 4, 5]:  # Permitir cambiar estas columnas
            item = fields_table.item(row_id, 'values')
            item_list = toggle_value(
                item, col_num, [CHECKBOX_TICKED, CHECKBOX_UNTICKED])
            fields_table.item(row_id, values=item_list)
            update_field_data(row_id, col_num, item_list[col_num])
    elif region == 'heading':
        return "break"


def update_field_data(row_id, col_index, value):
    field_name = fields_table.item(row_id, 'values')[0]
    field_info = next(
        (field for field in fields if field['name'] == field_name), None)
    if field_info:
        if col_index == 3:
            field_info['primary_key'] = (value == CHECKBOX_TICKED)
        elif col_index == 4:
            field_info['nullable'] = (value == CHECKBOX_TICKED)
        elif col_index == 5:
            field_info['mandatory'] = (value == CHECKBOX_TICKED)


def edit_field_details(event):
    region = fields_table.identify_region(event.x, event.y)
    if region != 'cell':
        return
    col = fields_table.identify_column(event.x)
    row_id = fields_table.identify_row(event.y)
    col_num = int(col.strip('#')) - 1
    if col_num == 1 or col_num == 2:  # Permite editar Type o Size
        item = fields_table.item(row_id, 'values')
        field_name = fields_table.item(row_id, 'values')[0]
        new_value = simpledialog.askstring(
            "Edit Value", f"Enter new value for {field_name}:", parent=app)
        if new_value is not None:
            item_list = list(item)
            item_list[col_num] = new_value
            fields_table.item(row_id, values=item_list)
            update_field_data_type_size(row_id, col_num, new_value)


def update_field_data_type_size(row_id, col_num, value):
    field_name = fields_table.item(row_id, 'values')[0]
    field_info = next(
        (field for field in fields if field['name'] == field_name), None)
    if field_info:
        if col_num == 1:  # Type
            field_info['type'] = value
        elif col_num == 2:  # Size
            field_info['size'] = value


def process_sql_and_update():
    sql = sql_input_text.get("1.0", tk.END)
    global table_name, fields
    table_name, fields = parse_sql_table(sql)
    load_fields_into_ui(fields)


def load_fields_into_ui(fields):
    for i in fields_table.get_children():
        fields_table.delete(i)
    for field in fields:
        fields_table.insert('', 'end', values=(
            field['name'],
            field['type'],
            field['size'],
            CHECKBOX_TICKED if field['primary_key'] else CHECKBOX_UNTICKED,
            CHECKBOX_TICKED if field['nullable'] else CHECKBOX_UNTICKED,
            CHECKBOX_TICKED if field['mandatory'] else CHECKBOX_UNTICKED
        ))


def process_sql_and_update():
    sql = sql_input_text.get("1.0", tk.END)
    global table_name, fields
    try:
        # Llamar a parse_sql_table dentro del bloque try
        table_name, fields = parse_sql_table(sql)
        load_fields_into_ui(fields)
    except SQLParsingError as e:
        # Capturar la excepción SQLParsingError y mostrar el mensaje de error en pantalla
        messagebox.showerror("SQL Parsing Error", str(e))


# GUI setup
app = tk.Tk()
app.title("CRUD Generator for Laravel")

# Definir los estilos para los botones con colores personalizados
style = ttk.Style()
style.configure('Pastel.TButton', borderwidth=0, width=20)

style.configure('Button1.TButton', background='#47E72E')
style.configure('Button2.TButton', background='#87CEEB')
style.configure('Button3.TButton', background='#87CEEB')
style.configure('Button4.TButton', background='#FFD700')

# SQL input area
sql_input_frame = tk.Frame(app)
sql_input_frame.pack(fill='x', padx=10, pady=10)
sql_input_label = tk.Label(sql_input_frame, text="SQL Statement:")
sql_input_label.pack(side='left')
sql_input_text = tk.Text(sql_input_frame, height=10)
sql_input_text.pack(side='left', fill='x', expand=True)

# Button to process SQL input
process_button = ttk.Button(
    app, text="Process SQL", command=process_sql_and_update, style='Button1.TButton')
process_button.pack(pady=5)

# Table to display detected fields
fields_frame = tk.LabelFrame(app, text="Fields")
fields_frame.pack(fill='both', expand=True, padx=10, pady=10)
fields_table = ttk.Treeview(fields_frame, columns=(
    'name', 'type', 'size', 'primary_key', 'nullable', 'mandatory'), show='headings')

for col in fields_table['columns']:
    fields_table.heading(col, text=col.capitalize())
    fields_table.column(col, anchor='center', width=120)
fields_table.pack(fill='both', expand=True)

# Nuevo frame para organizar los botones en una sola fila
buttons_frame = tk.Frame(app)
buttons_frame.pack(fill='x', padx=10, pady=1)


# Organiza los botones lado a lado dentro del frame buttons_frame
create_crud_files_button = ttk.Button(buttons_frame, text="Create CRUD Files", command=lambda: request_directory_and_create_files(
    table_name.lower(), fields), style='Button2.TButton')
create_crud_files_button.pack(side='left', fill='x', expand=True, padx=2)

create_controller_button = ttk.Button(buttons_frame, text="Create Controller",
                                      command=lambda: create_controller(table_name, fields), style='Button3.TButton')
create_controller_button.pack(side='left', fill='x', expand=True, padx=2)

generate_model_button = ttk.Button(buttons_frame, text="Generate Model", command=lambda: generate_model(
    table_name, fields), style='Button4.TButton')
generate_model_button.pack(side='left', fill='x', expand=True, padx=2)

generate_migration_button = ttk.Button(
    buttons_frame, text="Generate Migration", command=generate_migration_only, style='Button4.TButton')
generate_migration_button.pack(side='left', fill='x', expand=True, padx=2)

generate_routes_button = ttk.Button(
    buttons_frame, text="Generate Routes", command=generate_routes, style='Button4.TButton')
generate_routes_button.pack(side='left', fill='x', expand=True, padx=2)

# Add bindings for click to toggle and double-click to edit
fields_table.bind('<Button-1>', on_field_click)
fields_table.bind('<Double-Button-1>', edit_field_details)

app.mainloop()
