from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

class Board:

    def __init__(self, perspective):
        self.perspective = perspective
        self.window = 0
        self.width = 1200
        self.height = 1200
        self.title = "Chessica"

    def refresh2d(self, width, height):
        # This function tells OpenGL to draw things in 2D
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, width, 0.0, height, 0.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def draw_rect(self, x, y, width, height):
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + width, y)
        glVertex2f(x + width, y + height)
        glVertex2f(x, y + height)
        glEnd()

    def color_white(self):
        glColor3f(0, 0, 0)

    def color_black(self):
        glColor3f(1, 1, 1)

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # clear screen
        glLoadIdentity()  # reset position
        self.refresh2d(self.width, self.height)

        for y in range(8):
            for x in range(8):
                total = x+y
                if total % 2 == 0:
                    glColor3f(0, 0, 0)
                else:
                    glColor3f(1, 1, 1)
                self.draw_rect(150*x, 150*y, 150, 150)

        glutSwapBuffers()

    def init_gl(self):
        # initialization
        glutInit()  # initialize glut
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH)
        glutInitWindowSize(self.width, self.height)  # set window size
        glutInitWindowPosition(0, 0)  # set window position
        window = glutCreateWindow(self.title)  # create window with title
        glutDisplayFunc(self.draw)  # set draw function callback
        print("Drawing Board")
        glutIdleFunc(self.draw)  # draw all the time
        glutMainLoop()
