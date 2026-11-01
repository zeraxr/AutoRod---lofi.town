import tkinter as tk
from tkinter import ttk


class DiagnosticsCanvasView(ttk.Frame):
    """
    Componente visual de Tkinter que aloja el Canvas de diagnósticos 'Rayos X'.
    Opera exclusivamente en el hilo principal de la UI.
    Garantiza cero fugas de memoria, diseño responsivo y centrado automático continuo.
    """

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self.canvas = tk.Canvas(
            self,
            width=640,
            height=480,
            bg="#08090d",
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._current_photo: tk.PhotoImage | None = None
        self._image_item_id: int | None = None

        # Escuchar evento de redimensionamiento dinámico
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def _on_canvas_resize(self, event: tk.Event) -> None:
        """Mantiene la imagen perfectamente centrada al cambiar el tamaño de la ventana."""
        if self._image_item_id is not None and self._current_photo is not None:
            photo_w = self._current_photo.width()
            photo_h = self._current_photo.height()
            pos_x = max(0, (event.width - photo_w) // 2) if event.width > photo_w else 0
            pos_y = max(0, (event.height - photo_h) // 2) if event.height > photo_h else 0
            self.canvas.coords(self._image_item_id, pos_x, pos_y)

    def update_image(self, img_data: bytes) -> None:
        """
        Recibe el buffer binario en formato PPM, genera el PhotoImage
        y actualiza el Canvas sin acumular objetos ni bloquear la UI.
        """
        new_photo = tk.PhotoImage(data=img_data)
        photo_w = new_photo.width()
        photo_h = new_photo.height()

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        # Centrar la imagen en el espacio disponible
        pos_x = max(0, (canvas_w - photo_w) // 2) if canvas_w > photo_w else 0
        pos_y = max(0, (canvas_h - photo_h) // 2) if canvas_h > photo_h else 0

        if self._image_item_id is None:
            self._image_item_id = self.canvas.create_image(
                pos_x, pos_y, anchor=tk.NW, image=new_photo
            )
        else:
            self.canvas.coords(self._image_item_id, pos_x, pos_y)
            self.canvas.itemconfig(self._image_item_id, image=new_photo)

        # Retención explícita para evitar recolección de basura prematura en Tkinter
        self._current_photo = new_photo
