import skia


class Smiley:
    def __init__(self, center: tuple[int, int], radius: int):
        self.center = center
        self.radius = radius

    def draw(self, canvas: skia.Canvas) -> None:
        cx, cy = float(self.center[0]), float(self.center[1])
        r = float(self.radius)

        fill = skia.Paint(AntiAlias=True, Color=skia.Color(255, 220, 0))
        stroke = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0),
                            Style=skia.Paint.kStroke_Style, StrokeWidth=2)

        # Face
        canvas.drawCircle(cx, cy, r, fill)
        canvas.drawCircle(cx, cy, r, stroke)

        # Eyes
        eye_y = cy - r / 4
        eye_x = r / 3
        eye_r = max(r / 10, 3)
        eye_paint = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0))
        canvas.drawCircle(cx - eye_x, eye_y, eye_r, eye_paint)
        canvas.drawCircle(cx + eye_x, eye_y, eye_r, eye_paint)

        # Smile — bottom half of an ellipse
        smile_rect = skia.Rect.MakeLTRB(cx - r / 2, cy - r / 6, cx + r / 2, cy + r / 2)
        canvas.drawArc(smile_rect, 0, 180, False, stroke)
