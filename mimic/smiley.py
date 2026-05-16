import skia


class Smiley:
    eye_blink_left = 0.0
    eye_blink_right = 0.0

    def __init__(self, center: tuple[int, int], radius: int):
        self.center = center
        self.radius = radius

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
        
        canvas.drawCircle(64, 64, 62, bg_fill)
        canvas.drawCircle(64, 64, 62, stroke)

        if self.eye_blink_left < 0.5:
            canvas.drawOval(skia.Rect.MakeXYWH(74, 38, 20, 36), fg_fill)
        
        if self.eye_blink_right < 0.5:
            canvas.drawOval(skia.Rect.MakeXYWH(34, 38, 20, 36), fg_fill)
        
        canvas.drawPath(mouth_path, paint)
