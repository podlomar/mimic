import skia

def draw_eye(canvas: skia.Canvas, blink: float, side) -> None:
    paint = skia.Paint(AntiAlias=True, Color=skia.Color(50, 50, 50))

    x = 34 if side == "right" else 74
    y = int(38 + 22 * blink)
    w = 20
    h = int(36 - 36 * blink)

    canvas.drawOval(skia.Rect.MakeXYWH(x, y, w, h), paint)

class Smiley:
    eye_blink_left = 0.0
    eye_blink_right = 0.0
    tilt = 0.0   # degrees, positive = clockwise
    scale = 1.0

    def __init__(self, cx: int, cy: int):
        self.cx = cx
        self.cy = cy

    def draw(self, canvas: skia.Canvas) -> None:
        bg_fill = skia.Paint(AntiAlias=True, Color=skia.Color(255, 200, 30))
        fg_fill = skia.Paint(AntiAlias=True, Color=skia.Color(50, 50, 50))

        stroke = skia.Paint(AntiAlias=True, Color=skia.Color(50, 50, 50),
                            Style=skia.Paint.kStroke_Style, StrokeWidth=4)


        mouth_path = skia.Path()
        mouth_path.moveTo(32, 88)
        mouth_path.rCubicTo(16, 20, 48, 20, 64, 0)

        paint = skia.Paint(
            AntiAlias=True,
            Style=skia.Paint.kStroke_Style,
            StrokeCap=skia.Paint.kRound_Cap,
            StrokeWidth=6,
        )
        
        canvas.save()
        canvas.translate(self.cx, self.cy)
        canvas.rotate(self.tilt)
        canvas.scale(self.scale, self.scale)
        canvas.translate(-64, -64)

        canvas.drawCircle(64, 64, 62, bg_fill)
        canvas.drawCircle(64, 64, 62, stroke)

        draw_eye(canvas, self.eye_blink_left, "left")
        draw_eye(canvas, self.eye_blink_right, "right")

        canvas.drawPath(mouth_path, paint)

        canvas.restore()
