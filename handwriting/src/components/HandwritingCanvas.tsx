import React, {
  useState,
  useRef,
  useImperativeHandle,
  forwardRef,
  useCallback,
  useEffect,
  useMemo,
} from 'react';
import {
  View,
  StyleSheet,
  PanResponder,
  Platform,
} from 'react-native';
import Svg, { Path } from 'react-native-svg';
import { Point, Stroke, Strokes } from '../types/handwriting';

export interface HandwritingCanvasRef {
  clear: () => void;
  undo: () => void;
  getStrokes: () => Strokes;
}

export interface HandwritingCanvasProps {
  size?: number;
  strokeColor?: string;
  strokeWidth?: number;
  onStrokeEnd?: (strokes: Strokes) => void;
  onStrokesChange?: (strokes: Strokes) => void;
  children?: React.ReactNode;
}

export const HandwritingCanvas = forwardRef<HandwritingCanvasRef, HandwritingCanvasProps>(
  (
    {
      size = 320,
      strokeColor = '#38bdf8',
      strokeWidth = 4.5,
      onStrokeEnd,
      onStrokesChange,
      children,
    },
    ref
  ) => {
    const [strokes, setStrokes] = useState<Strokes>([]);
    const [currentStroke, setCurrentStroke] = useState<Stroke>([]);

    const strokesRef = useRef<Strokes>([]);
    const currentStrokeRef = useRef<Stroke>([]);
    const sizeRef = useRef(size);
    sizeRef.current = size;
    const previousSizeRef = useRef(size);
    const callbacksRef = useRef({ onStrokeEnd, onStrokesChange });
    callbacksRef.current = { onStrokeEnd, onStrokesChange };
    const drawFrameRef = useRef<number | null>(null);

    useEffect(() => () => {
      if (drawFrameRef.current !== null) cancelAnimationFrame(drawFrameRef.current);
    }, []);

    useEffect(() => {
      const previous = previousSizeRef.current;
      if (previous === size) return;
      previousSizeRef.current = size;
      const scale = (size - 48) / Math.max(1, previous - 48);
      const resizePoint = (point: Point): Point => ({
        ...point,
        x: 24 + (point.x - 24) * scale,
        y: 24 + (point.y - 24) * scale,
      });
      const resized = strokesRef.current.map(stroke => stroke.map(resizePoint));
      strokesRef.current = resized;
      setStrokes(resized);
      const resizedCurrent = currentStrokeRef.current.map(resizePoint);
      currentStrokeRef.current = resizedCurrent;
      setCurrentStroke(resizedCurrent);
    }, [size]);

    const clear = useCallback(() => {
      setStrokes([]);
      setCurrentStroke([]);
      if (drawFrameRef.current !== null) cancelAnimationFrame(drawFrameRef.current);
      drawFrameRef.current = null;
      strokesRef.current = [];
      currentStrokeRef.current = [];
      onStrokesChange?.([]);
      onStrokeEnd?.([]);
    }, [onStrokeEnd, onStrokesChange]);

    const undo = useCallback(() => {
      const next = strokesRef.current.slice(0, -1);
      strokesRef.current = next;
      setStrokes(next);
      callbacksRef.current.onStrokesChange?.(next);
      callbacksRef.current.onStrokeEnd?.(next);
    }, []);

    useImperativeHandle(
      ref,
      () => ({
        clear,
        undo,
        getStrokes: () => strokesRef.current,
      }),
      [clear, undo]
    );

    // Mobile PanResponder
    const panResponder = useMemo(
      () => PanResponder.create({
        onStartShouldSetPanResponder: () => true,
        onMoveShouldSetPanResponder: () => true,
        onPanResponderGrant: evt => {
          const { locationX, locationY } = evt.nativeEvent;
          const x = Math.max(0, Math.min(sizeRef.current, locationX));
          const y = Math.max(0, Math.min(sizeRef.current, locationY));
          const pt: Point = { x, y, t: Date.now() };
          currentStrokeRef.current = [pt];
          setCurrentStroke([pt]);
        },
        onPanResponderMove: evt => {
          const { locationX, locationY } = evt.nativeEvent;
          const x = Math.max(0, Math.min(sizeRef.current, locationX));
          const y = Math.max(0, Math.min(sizeRef.current, locationY));
          const pt: Point = { x, y, t: Date.now() };
          if (currentStrokeRef.current.length < 384) currentStrokeRef.current.push(pt);
          if (drawFrameRef.current === null) {
            drawFrameRef.current = requestAnimationFrame(() => {
              drawFrameRef.current = null;
              setCurrentStroke([...currentStrokeRef.current]);
            });
          }
        },
        onPanResponderRelease: () => {
          if (currentStrokeRef.current.length > 0) {
            const newStrokes = [...strokesRef.current, [...currentStrokeRef.current]];
            strokesRef.current = newStrokes;
            setStrokes(newStrokes);
            setCurrentStroke([]);
            currentStrokeRef.current = [];
            callbacksRef.current.onStrokesChange?.(newStrokes);
            callbacksRef.current.onStrokeEnd?.(newStrokes);
          }
        },
        onPanResponderTerminate: () => {
          currentStrokeRef.current = [];
          setCurrentStroke([]);
        },
      }),
      []
    );

    // Web mouse/touch handlers for seamless cross-platform browser support
    const isDrawingWebRef = useRef(false);

    const handleWebMouseDown = (e: any) => {
      if (Platform.OS !== 'web') return;
      isDrawingWebRef.current = true;
      const rect = e.currentTarget.getBoundingClientRect();
      const x = Math.max(0, Math.min(size, e.clientX - rect.left));
      const y = Math.max(0, Math.min(size, e.clientY - rect.top));
      const pt: Point = { x, y, t: Date.now() };
      currentStrokeRef.current = [pt];
      setCurrentStroke([pt]);
    };

    const handleWebMouseMove = (e: any) => {
      if (Platform.OS !== 'web' || !isDrawingWebRef.current) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const x = Math.max(0, Math.min(size, e.clientX - rect.left));
      const y = Math.max(0, Math.min(size, e.clientY - rect.top));
      const pt: Point = { x, y, t: Date.now() };
      const updated = [...currentStrokeRef.current, pt];
      currentStrokeRef.current = updated;
      setCurrentStroke(updated);
    };

    const handleWebMouseUp = () => {
      if (Platform.OS !== 'web' || !isDrawingWebRef.current) return;
      isDrawingWebRef.current = false;
      if (currentStrokeRef.current.length > 0) {
        const newStrokes = [...strokesRef.current, currentStrokeRef.current];
        strokesRef.current = newStrokes;
        setStrokes(newStrokes);
        setCurrentStroke([]);
        currentStrokeRef.current = [];
        onStrokesChange?.(newStrokes);
        onStrokeEnd?.(newStrokes);
      }
    };

    // Builds SVG path command from array of points
    const strokeToSvgPath = (stroke: Stroke): string => {
      if (stroke.length === 0) return '';
      if (stroke.length === 1) {
        return `M ${stroke[0].x} ${stroke[0].y} L ${stroke[0].x + 0.1} ${stroke[0].y + 0.1}`;
      }

      let d = `M ${stroke[0].x} ${stroke[0].y}`;
      for (let i = 1; i < stroke.length; i++) {
        // Quadratic bezier smoothing
        const p1 = stroke[i - 1];
        const p2 = stroke[i];
        const midX = (p1.x + p2.x) / 2;
        const midY = (p1.y + p2.y) / 2;
        d += ` Q ${p1.x} ${p1.y}, ${midX} ${midY}`;
      }
      d += ` L ${stroke[stroke.length - 1].x} ${stroke[stroke.length - 1].y}`;
      return d;
    };

    const webProps =
      Platform.OS === 'web'
        ? {
            onMouseDown: handleWebMouseDown,
            onMouseMove: handleWebMouseMove,
            onMouseUp: handleWebMouseUp,
            onMouseLeave: handleWebMouseUp,
            onTouchStart: (e: any) => {
              if (e.cancelable) e.preventDefault();
              const touch = e.touches[0];
              const rect = e.currentTarget.getBoundingClientRect();
              handleWebMouseDown({
                clientX: touch.clientX,
                clientY: touch.clientY,
                currentTarget: e.currentTarget,
              });
            },
            onTouchMove: (e: any) => {
              if (e.cancelable) e.preventDefault();
              const touch = e.touches[0];
              const rect = e.currentTarget.getBoundingClientRect();
              handleWebMouseMove({
                clientX: touch.clientX,
                clientY: touch.clientY,
                currentTarget: e.currentTarget,
              });
            },
            onTouchEnd: (e: any) => {
              if (e.cancelable) e.preventDefault();
              handleWebMouseUp();
            },
          }
        : {};

    return (
      <View
        style={[styles.container, { width: size, height: size }]}
        {...(Platform.OS === 'web' ? webProps : panResponder.panHandlers)}
      >
        {/* Child overlay layer (e.g. ghost SVG guide) */}
        {children && <View style={StyleSheet.absoluteFill}>{children}</View>}

        {/* User Drawn Strokes */}
        <Svg width={size} height={size} style={StyleSheet.absoluteFill}>
          {strokes.map((stroke, index) => (
            <Path
              key={`stroke-${index}`}
              d={strokeToSvgPath(stroke)}
              stroke={strokeColor}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
          ))}
          {currentStroke.length > 0 && (
            <Path
              d={strokeToSvgPath(currentStroke)}
              stroke={strokeColor}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
          )}
        </Svg>
      </View>
    );
  }
);

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#0d1117',
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#30363d',
    alignSelf: 'center',
    touchAction: 'none',
    userSelect: 'none',
    cursor: 'crosshair',
  } as any,
});

