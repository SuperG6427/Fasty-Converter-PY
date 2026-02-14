#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fasty Converter
Script para conversion rapida de imagenes entre multiples formatos
"""

import os
import sys
import glob
from pathlib import Path
from datetime import datetime

# Verificar e instalar dependencias
required_packages = ['Pillow', 'rich', 'questionary']
missing_packages = []

for package in required_packages:
    try:
        if package == 'Pillow':
            __import__('PIL')
        else:
            __import__(package.lower().replace('-', '_'))
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print("Instalando dependencias faltantes...")
    import subprocess
    for package in missing_packages:
        package_name = 'pillow' if package == 'Pillow' else package
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
    print("Dependencias instaladas. Reiniciando el script...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

from PIL import Image, UnidentifiedImageError
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich import box
import questionary
from questionary import Style
import shutil

# Estilo para questionary
custom_style = Style([
    ('question', 'bold fg:cyan'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:yellow bold'),
    ('highlighted', 'fg:magenta bold'),
    ('selected', 'fg:green'),
])

console = Console()

class FasterImageConverter:
    def __init__(self):
        self.supported_formats = {
            'JPEG': ['jpg', 'jpeg', 'jpe', 'jfif'],
            'PNG': ['png'],
            'BMP': ['bmp'],
            'WEBP': ['webp'],
            'TIFF': ['tiff', 'tif'],
            'RAW': ['raw', 'arw', 'cr2', 'nef', 'dng'],
            'HEIF': ['heif', 'heic']
        }
        
        self.extension_to_format = {}
        for fmt, exts in self.supported_formats.items():
            for ext in exts:
                self.extension_to_format[ext] = fmt
        
        self.current_folder = os.getcwd()
        self.source_folder = self.current_folder
        self.destination_folder = self.current_folder
        self.selected_images = []
        self.conversion_stats = {'success': 0, 'failed': 0, 'skipped': 0}
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_banner(self):
        self.clear_screen()
        banner = """
        ╔══════════════════════════════════════════════════════════════╗
        ║                        FASTY CONVERTER                       ║
        ║                 Conversor Rapido de Imagenes                 ║
        ╚══════════════════════════════════════════════════════════════╝
        """
        console.print(Panel.fit(banner, style="bold cyan"))
        console.print()
    
    def display_main_menu(self):
        self.display_banner()
        
        menu = Table(show_header=False, box=box.ROUNDED, style="cyan")
        menu.add_column("Opcion", style="cyan", width=15)
        menu.add_column("Descripcion", style="white")
        
        options = [
            ("1", "Seleccionar carpeta origen"),
            ("2", "Seleccionar carpeta destino"),
            ("3", "Ver imagenes"),
            ("4", "Convertir imagenes"),
            ("5", "Configurar opciones"),
            ("6", "Ver estadisticas"),
            ("7", "Ayuda"),
            ("8", "Salir")
        ]
        
        for opt, desc in options:
            menu.add_row(opt, desc)
        
        console.print(Panel(menu, title="[bold]Menu Principal[/bold]", border_style="cyan"))
        console.print()
        
        info = Panel.fit(
            f"[bold]Origen:[/bold] {self.source_folder}\n"
            f"[bold]Destino:[/bold] {self.destination_folder}\n"
            f"[bold]Seleccionadas:[/bold] {len(self.selected_images)}",
            title="[bold]Info Actual[/bold]", border_style="green"
        )
        console.print(info)
        console.print()
    
    def select_source_folder(self):
        console.print("\n[bold cyan]Seleccion carpeta origen[/bold cyan]")
        new_folder = Prompt.ask(
            f"[green]Actual:[/green] {self.source_folder}\n"
            "[cyan]Nueva ruta[/cyan] (Enter para mantener)",
            default=self.source_folder
        )
        
        if os.path.isdir(new_folder):
            self.source_folder = os.path.abspath(new_folder)
            console.print(f"[green]✓ Origen:[/green] {self.source_folder}")
            self.selected_images = []
        else:
            console.print("[red]✗ Carpeta no existe[/red]")
        
        input("\nPresiona Enter para continuar...")
    
    def select_destination_folder(self):
        console.print("\n[bold cyan]Seleccion carpeta destino[/bold cyan]")
        new_folder = Prompt.ask(
            f"[green]Actual:[/green] {self.destination_folder}\n"
            "[cyan]Nueva ruta[/cyan] (Enter para mantener)",
            default=self.destination_folder
        )
        
        if os.path.isdir(new_folder):
            self.destination_folder = os.path.abspath(new_folder)
            console.print(f"[green]✓ Destino:[/green] {self.destination_folder}")
        else:
            if Confirm.ask("[yellow]Crear carpeta?[/yellow]"):
                os.makedirs(new_folder, exist_ok=True)
                self.destination_folder = os.path.abspath(new_folder)
                console.print(f"[green]✓ Creada:[/green] {self.destination_folder}")
        
        input("\nPresiona Enter para continuar...")
    
    def detect_images_in_folder(self, folder=None):
        folder = folder or self.source_folder
        image_files = []
        extensions = sum(self.supported_formats.values(), [])
        
        for ext in extensions:
            image_files.extend(glob.glob(os.path.join(folder, f'*.{ext}'), recursive=False))
        
        return sorted(image_files)
    
    def display_images_in_folder(self):
        self.clear_screen()
        console.print(Panel.fit("[bold cyan]Imagenes disponibles[/bold cyan]", border_style="cyan"))
        
        images = self.detect_images_in_folder()
        
        if not images:
            console.print("[yellow]No se encontraron imagenes[/yellow]")
            console.print(f"[white]Carpeta: {self.source_folder}[/white]")
            console.print("\n[cyan]Formatos:[/cyan]")
            for fmt, exts in self.supported_formats.items():
                console.print(f"  • {fmt}: {', '.join(exts)}")
            input("\nPresiona Enter para continuar...")
            return
        
        table = Table(title=f"Imagenes encontradas ({len(images)})", box=box.ROUNDED)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Nombre", style="white")
        table.add_column("Extension", style="green")
        table.add_column("Tamano", style="yellow")
        table.add_column("Sel", style="magenta")
        
        for i, path in enumerate(images, 1):
            name, ext = os.path.splitext(os.path.basename(path))
            ext = ext[1:].lower()
            size = os.path.getsize(path) if os.path.exists(path) else 0
            size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/(1024*1024):.1f}MB"
            selected = "✓" if path in self.selected_images else ""
            table.add_row(str(i), name[:30], ext, size_str, selected)
        
        console.print(table)
        console.print("\n[bold cyan]Opciones:[/bold cyan]")
        console.print("  [green]s[/green] - Seleccionar")
        console.print("  [green]a[/green] - Todo")
        console.print("  [green]n[/green] - Ninguno")
        console.print("  [green]q[/green] - Volver")
        
        choice = Prompt.ask("\n[cyan]Opcion[/cyan]", choices=['s', 'a', 'n', 'q'], default='q')
        
        if choice == 's':
            selected = questionary.checkbox(
                "Selecciona imagenes:",
                choices=[questionary.Choice(os.path.basename(p), value=p, checked=p in self.selected_images) 
                        for p in images],
                style=custom_style
            ).ask()
            if selected:
                self.selected_images = selected
        elif choice == 'a':
            self.selected_images = images.copy()
        elif choice == 'n':
            self.selected_images = []
        
        console.print(f"[green]✓ {len(self.selected_images)} seleccionadas[/green]")
        input("\nPresiona Enter para continuar...")
    
    def get_valid_quality(self):
        """Obtiene un valor de calidad valido del usuario"""
        while True:
            try:
                q = input("Calidad (1-100) [85]: ").strip()
                if q == "":
                    return 85
                q = int(q)
                if 1 <= q <= 100:
                    return q
                else:
                    console.print("[red]Error: Debe ser entre 1 y 100[/red]")
            except ValueError:
                console.print("[red]Error: Ingrese un numero valido[/red]")
    
    def convert_images(self):
        if not self.selected_images:
            console.print("[yellow]No hay imagenes seleccionadas[/yellow]")
            input("\nPresiona Enter para continuar...")
            return
        
        self.clear_screen()
        console.print(Panel.fit("[bold cyan]Convertir Imagenes[/bold cyan]", border_style="cyan"))
        
        fmt = questionary.select("Formato destino:", choices=list(self.supported_formats.keys())).ask()
        if not fmt: return
        
        quality = 85
        if fmt in ['JPEG', 'WEBP']:
            console.print("\n[cyan]Configuracion de calidad:[/cyan]")
            quality = self.get_valid_quality()
        
        preserve = Confirm.ask("Preservar metadatos?", default=True)
        overwrite = Confirm.ask("Sobrescribir?", default=False)
        
        console.print(f"\n[bold yellow]Resumen:[/bold yellow]")
        console.print(f"• Imagenes: {len(self.selected_images)}")
        console.print(f"• Formato: {fmt}")
        if fmt in ['JPEG', 'WEBP']:
            console.print(f"• Calidad: {quality}")
        console.print(f"• Destino: {self.destination_folder}")
        
        if not Confirm.ask("\n[cyan]Continuar?[/cyan]"):
            console.print("[yellow]Cancelado[/yellow]")
            input("\nPresiona Enter para continuar...")
            return
        
        self.conversion_stats = {'success': 0, 'failed': 0, 'skipped': 0}
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                     BarColumn(), console=console) as progress:
            task = progress.add_task("[cyan]Convirtiendo...", total=len(self.selected_images))
            
            for path in self.selected_images:
                try:
                    with Image.open(path) as img:
                        info = img.info.copy() if preserve else {}
                        target_ext = self.supported_formats[fmt][0]
                        name = os.path.splitext(os.path.basename(path))[0]
                        target = os.path.join(self.destination_folder, f"{name}.{target_ext}")
                        
                        if os.path.exists(target) and not overwrite:
                            n = 1
                            while os.path.exists(target):
                                target = os.path.join(self.destination_folder, f"{name}_{n}.{target_ext}")
                                n += 1
                        
                        params = {'quality': quality} if fmt in ['JPEG', 'WEBP'] else {}
                        if fmt == 'TIFF':
                            params['compression'] = 'tiff_lzw'
                        if fmt == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        img.save(target, format=fmt, **params, **info)
                        self.conversion_stats['success'] += 1
                        console.print(f"[green]✓ {os.path.basename(target)}[/green]")
                except Exception as e:
                    console.print(f"[red]✗ Error: {os.path.basename(path)} - {str(e)[:50]}[/red]")
                    self.conversion_stats['failed'] += 1
                progress.update(task, advance=1)
        
        console.print(f"\n[green]✓ Correctas: {self.conversion_stats['success']}[/green]")
        console.print(f"[red]✗ Fallidas: {self.conversion_stats['failed']}[/red]")
        input("\nPresiona Enter para continuar...")
    
    def display_statistics(self):
        self.clear_screen()
        images = self.detect_images_in_folder()
        total = sum(os.path.getsize(p) for p in images if os.path.exists(p))
        
        stats = Table(title="Estadisticas", box=box.ROUNDED)
        stats.add_column("Metrica", style="cyan")
        stats.add_column("Valor", style="white")
        stats.add_row("Origen", self.source_folder)
        stats.add_row("Imagenes", str(len(images)))
        stats.add_row("Tamano", f"{total/(1024*1024):.1f}MB")
        stats.add_row("Seleccionadas", str(len(self.selected_images)))
        stats.add_row("Exitosas", str(self.conversion_stats['success']))
        stats.add_row("Fallidas", str(self.conversion_stats['failed']))
        
        console.print(Panel(stats, title="[bold]Estadisticas[/bold]", border_style="cyan"))
        input("\nPresiona Enter para continuar...")
    
    def display_help(self):
        self.clear_screen()
        help_text = """
[bold cyan]FASTERIMAGE CONVERTER - AYUDA[/bold cyan]

[bold]Uso:[/bold]
1. Selecciona carpeta origen
2. Selecciona carpeta destino
3. Visualiza y selecciona imagenes
4. Convierte

[bold]Formatos:[/bold]
• JPEG (.jpg, .jpeg, .jfif)
• PNG (.png)
• BMP (.bmp)
• WEBP (.webp)
• TIFF (.tiff, .tif)
• RAW (.raw, .arw, .cr2, .nef, .dng)
• HEIF (.heif, .heic)

[bold]Atajos:[/bold]
• q - Cancelar/Volver
• Enter - Confirmar
• Flechas - Navegar
        """
        console.print(Panel(help_text, title="[bold]Ayuda[/bold]", border_style="cyan"))
        input("\nPresiona Enter para continuar...")
    
    def run(self):
        while True:
            try:
                self.display_main_menu()
                choice = Prompt.ask("[bold cyan]Opcion (1-8)[/bold cyan]", 
                                   choices=[str(i) for i in range(1,9)], default='8')
                
                if choice == '8':
                    if Confirm.ask("[red]Salir?[/red]"):
                        console.print("[green]¡Hasta luego![/green]")
                        break
                elif choice == '1':
                    self.select_source_folder()
                elif choice == '2':
                    self.select_destination_folder()
                elif choice == '3':
                    self.display_images_in_folder()
                elif choice == '4':
                    self.convert_images()
                elif choice == '5':
                    console.print("[yellow]Opciones disponibles durante la conversion[/yellow]")
                    input("\nPresiona Enter para continuar...")
                elif choice == '6':
                    self.display_statistics()
                elif choice == '7':
                    self.display_help()
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Operacion cancelada[/yellow]")
                if Confirm.ask("[red]Salir?[/red]"):
                    break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                input("\nPresiona Enter para continuar...")

def main():
    try:
        converter = FasterImageConverter()
        converter.run()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Programa terminado[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error critico: {e}[/red]")

if __name__ == "__main__":
    main()