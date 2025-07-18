import {
  require_prop_types
} from "./chunk-MQBRFNOA.js";
import "./chunk-K7E3GE6C.js";
import {
  require_react
} from "./chunk-65KY755N.js";
import {
  __commonJS,
  __esm,
  __export,
  __toCommonJS
} from "./chunk-V4OQ3NZ2.js";

// node_modules/perfect-scrollbar/dist/perfect-scrollbar.esm.js
var perfect_scrollbar_esm_exports = {};
__export(perfect_scrollbar_esm_exports, {
  default: () => perfect_scrollbar_esm_default
});
function get(element) {
  return getComputedStyle(element);
}
function set(element, obj) {
  for (var key in obj) {
    var val = obj[key];
    if (typeof val === "number") {
      val = val + "px";
    }
    element.style[key] = val;
  }
  return element;
}
function div(className) {
  var div2 = document.createElement("div");
  div2.className = className;
  return div2;
}
function matches(element, query) {
  if (!elMatches) {
    throw new Error("No element matching method supported");
  }
  return elMatches.call(element, query);
}
function remove(element) {
  if (element.remove) {
    element.remove();
  } else {
    if (element.parentNode) {
      element.parentNode.removeChild(element);
    }
  }
}
function queryChildren(element, selector) {
  return Array.prototype.filter.call(
    element.children,
    function(child) {
      return matches(child, selector);
    }
  );
}
function addScrollingClass(i, x) {
  var classList = i.element.classList;
  var className = cls.state.scrolling(x);
  if (classList.contains(className)) {
    clearTimeout(scrollingClassTimeout[x]);
  } else {
    classList.add(className);
  }
}
function removeScrollingClass(i, x) {
  scrollingClassTimeout[x] = setTimeout(
    function() {
      return i.isAlive && i.element.classList.remove(cls.state.scrolling(x));
    },
    i.settings.scrollingThreshold
  );
}
function setScrollingClassInstantly(i, x) {
  addScrollingClass(i, x);
  removeScrollingClass(i, x);
}
function createEvent(name) {
  if (typeof window.CustomEvent === "function") {
    return new CustomEvent(name);
  }
  var evt = document.createEvent("CustomEvent");
  evt.initCustomEvent(name, false, false, void 0);
  return evt;
}
function processScrollDiff(i, axis, diff, useScrollingClass, forceFireReachEvent) {
  if (useScrollingClass === void 0) useScrollingClass = true;
  if (forceFireReachEvent === void 0) forceFireReachEvent = false;
  var fields;
  if (axis === "top") {
    fields = ["contentHeight", "containerHeight", "scrollTop", "y", "up", "down"];
  } else if (axis === "left") {
    fields = ["contentWidth", "containerWidth", "scrollLeft", "x", "left", "right"];
  } else {
    throw new Error("A proper axis should be provided");
  }
  processScrollDiff$1(i, diff, fields, useScrollingClass, forceFireReachEvent);
}
function processScrollDiff$1(i, diff, ref, useScrollingClass, forceFireReachEvent) {
  var contentHeight = ref[0];
  var containerHeight = ref[1];
  var scrollTop = ref[2];
  var y = ref[3];
  var up = ref[4];
  var down = ref[5];
  if (useScrollingClass === void 0) useScrollingClass = true;
  if (forceFireReachEvent === void 0) forceFireReachEvent = false;
  var element = i.element;
  i.reach[y] = null;
  if (element[scrollTop] < 1) {
    i.reach[y] = "start";
  }
  if (element[scrollTop] > i[contentHeight] - i[containerHeight] - 1) {
    i.reach[y] = "end";
  }
  if (diff) {
    element.dispatchEvent(createEvent("ps-scroll-" + y));
    if (diff < 0) {
      element.dispatchEvent(createEvent("ps-scroll-" + up));
    } else if (diff > 0) {
      element.dispatchEvent(createEvent("ps-scroll-" + down));
    }
    if (useScrollingClass) {
      setScrollingClassInstantly(i, y);
    }
  }
  if (i.reach[y] && (diff || forceFireReachEvent)) {
    element.dispatchEvent(createEvent("ps-" + y + "-reach-" + i.reach[y]));
  }
}
function toInt(x) {
  return parseInt(x, 10) || 0;
}
function isEditable(el) {
  return matches(el, "input,[contenteditable]") || matches(el, "select,[contenteditable]") || matches(el, "textarea,[contenteditable]") || matches(el, "button,[contenteditable]");
}
function outerWidth(element) {
  var styles = get(element);
  return toInt(styles.width) + toInt(styles.paddingLeft) + toInt(styles.paddingRight) + toInt(styles.borderLeftWidth) + toInt(styles.borderRightWidth);
}
function updateGeometry(i) {
  var element = i.element;
  var roundedScrollTop = Math.floor(element.scrollTop);
  var rect = element.getBoundingClientRect();
  i.containerWidth = Math.floor(rect.width);
  i.containerHeight = Math.floor(rect.height);
  i.contentWidth = element.scrollWidth;
  i.contentHeight = element.scrollHeight;
  if (!element.contains(i.scrollbarXRail)) {
    queryChildren(element, cls.element.rail("x")).forEach(function(el) {
      return remove(el);
    });
    element.appendChild(i.scrollbarXRail);
  }
  if (!element.contains(i.scrollbarYRail)) {
    queryChildren(element, cls.element.rail("y")).forEach(function(el) {
      return remove(el);
    });
    element.appendChild(i.scrollbarYRail);
  }
  if (!i.settings.suppressScrollX && i.containerWidth + i.settings.scrollXMarginOffset < i.contentWidth) {
    i.scrollbarXActive = true;
    i.railXWidth = i.containerWidth - i.railXMarginWidth;
    i.railXRatio = i.containerWidth / i.railXWidth;
    i.scrollbarXWidth = getThumbSize(i, toInt(i.railXWidth * i.containerWidth / i.contentWidth));
    i.scrollbarXLeft = toInt(
      (i.negativeScrollAdjustment + element.scrollLeft) * (i.railXWidth - i.scrollbarXWidth) / (i.contentWidth - i.containerWidth)
    );
  } else {
    i.scrollbarXActive = false;
  }
  if (!i.settings.suppressScrollY && i.containerHeight + i.settings.scrollYMarginOffset < i.contentHeight) {
    i.scrollbarYActive = true;
    i.railYHeight = i.containerHeight - i.railYMarginHeight;
    i.railYRatio = i.containerHeight / i.railYHeight;
    i.scrollbarYHeight = getThumbSize(
      i,
      toInt(i.railYHeight * i.containerHeight / i.contentHeight)
    );
    i.scrollbarYTop = toInt(
      roundedScrollTop * (i.railYHeight - i.scrollbarYHeight) / (i.contentHeight - i.containerHeight)
    );
  } else {
    i.scrollbarYActive = false;
  }
  if (i.scrollbarXLeft >= i.railXWidth - i.scrollbarXWidth) {
    i.scrollbarXLeft = i.railXWidth - i.scrollbarXWidth;
  }
  if (i.scrollbarYTop >= i.railYHeight - i.scrollbarYHeight) {
    i.scrollbarYTop = i.railYHeight - i.scrollbarYHeight;
  }
  updateCss(element, i);
  if (i.scrollbarXActive) {
    element.classList.add(cls.state.active("x"));
  } else {
    element.classList.remove(cls.state.active("x"));
    i.scrollbarXWidth = 0;
    i.scrollbarXLeft = 0;
    element.scrollLeft = i.isRtl === true ? i.contentWidth : 0;
  }
  if (i.scrollbarYActive) {
    element.classList.add(cls.state.active("y"));
  } else {
    element.classList.remove(cls.state.active("y"));
    i.scrollbarYHeight = 0;
    i.scrollbarYTop = 0;
    element.scrollTop = 0;
  }
}
function getThumbSize(i, thumbSize) {
  if (i.settings.minScrollbarLength) {
    thumbSize = Math.max(thumbSize, i.settings.minScrollbarLength);
  }
  if (i.settings.maxScrollbarLength) {
    thumbSize = Math.min(thumbSize, i.settings.maxScrollbarLength);
  }
  return thumbSize;
}
function updateCss(element, i) {
  var xRailOffset = { width: i.railXWidth };
  var roundedScrollTop = Math.floor(element.scrollTop);
  if (i.isRtl) {
    xRailOffset.left = i.negativeScrollAdjustment + element.scrollLeft + i.containerWidth - i.contentWidth;
  } else {
    xRailOffset.left = element.scrollLeft;
  }
  if (i.isScrollbarXUsingBottom) {
    xRailOffset.bottom = i.scrollbarXBottom - roundedScrollTop;
  } else {
    xRailOffset.top = i.scrollbarXTop + roundedScrollTop;
  }
  set(i.scrollbarXRail, xRailOffset);
  var yRailOffset = { top: roundedScrollTop, height: i.railYHeight };
  if (i.isScrollbarYUsingRight) {
    if (i.isRtl) {
      yRailOffset.right = i.contentWidth - (i.negativeScrollAdjustment + element.scrollLeft) - i.scrollbarYRight - i.scrollbarYOuterWidth - 9;
    } else {
      yRailOffset.right = i.scrollbarYRight - element.scrollLeft;
    }
  } else {
    if (i.isRtl) {
      yRailOffset.left = i.negativeScrollAdjustment + element.scrollLeft + i.containerWidth * 2 - i.contentWidth - i.scrollbarYLeft - i.scrollbarYOuterWidth;
    } else {
      yRailOffset.left = i.scrollbarYLeft + element.scrollLeft;
    }
  }
  set(i.scrollbarYRail, yRailOffset);
  set(i.scrollbarX, {
    left: i.scrollbarXLeft,
    width: i.scrollbarXWidth - i.railBorderXWidth
  });
  set(i.scrollbarY, {
    top: i.scrollbarYTop,
    height: i.scrollbarYHeight - i.railBorderYWidth
  });
}
function clickRail(i) {
  i.event.bind(i.scrollbarY, "mousedown", function(e) {
    return e.stopPropagation();
  });
  i.event.bind(i.scrollbarYRail, "mousedown", function(e) {
    var positionTop = e.pageY - window.pageYOffset - i.scrollbarYRail.getBoundingClientRect().top;
    var direction = positionTop > i.scrollbarYTop ? 1 : -1;
    i.element.scrollTop += direction * i.containerHeight;
    updateGeometry(i);
    e.stopPropagation();
  });
  i.event.bind(i.scrollbarX, "mousedown", function(e) {
    return e.stopPropagation();
  });
  i.event.bind(i.scrollbarXRail, "mousedown", function(e) {
    var positionLeft = e.pageX - window.pageXOffset - i.scrollbarXRail.getBoundingClientRect().left;
    var direction = positionLeft > i.scrollbarXLeft ? 1 : -1;
    i.element.scrollLeft += direction * i.containerWidth;
    updateGeometry(i);
    e.stopPropagation();
  });
}
function setupScrollHandlers(i) {
  bindMouseScrollHandler(i, [
    "containerHeight",
    "contentHeight",
    "pageY",
    "railYHeight",
    "scrollbarY",
    "scrollbarYHeight",
    "scrollTop",
    "y",
    "scrollbarYRail"
  ]);
  bindMouseScrollHandler(i, [
    "containerWidth",
    "contentWidth",
    "pageX",
    "railXWidth",
    "scrollbarX",
    "scrollbarXWidth",
    "scrollLeft",
    "x",
    "scrollbarXRail"
  ]);
}
function bindMouseScrollHandler(i, ref) {
  var containerDimension = ref[0];
  var contentDimension = ref[1];
  var pageAxis = ref[2];
  var railDimension = ref[3];
  var scrollbarAxis = ref[4];
  var scrollbarDimension = ref[5];
  var scrollAxis = ref[6];
  var axis = ref[7];
  var scrollbarRail = ref[8];
  var element = i.element;
  var startingScrollPosition = null;
  var startingMousePagePosition = null;
  var scrollBy = null;
  function moveHandler(e) {
    if (e.touches && e.touches[0]) {
      e[pageAxis] = e.touches[0]["page" + axis.toUpperCase()];
    }
    if (activeSlider === scrollbarAxis) {
      element[scrollAxis] = startingScrollPosition + scrollBy * (e[pageAxis] - startingMousePagePosition);
      addScrollingClass(i, axis);
      updateGeometry(i);
      e.stopPropagation();
      e.preventDefault();
    }
  }
  function endHandler() {
    removeScrollingClass(i, axis);
    i[scrollbarRail].classList.remove(cls.state.clicking);
    document.removeEventListener("mousemove", moveHandler);
    document.removeEventListener("mouseup", endHandler);
    document.removeEventListener("touchmove", moveHandler);
    document.removeEventListener("touchend", endHandler);
    activeSlider = null;
  }
  function bindMoves(e) {
    if (activeSlider === null) {
      activeSlider = scrollbarAxis;
      startingScrollPosition = element[scrollAxis];
      if (e.touches) {
        e[pageAxis] = e.touches[0]["page" + axis.toUpperCase()];
      }
      startingMousePagePosition = e[pageAxis];
      scrollBy = (i[contentDimension] - i[containerDimension]) / (i[railDimension] - i[scrollbarDimension]);
      if (!e.touches) {
        document.addEventListener("mousemove", moveHandler);
        document.addEventListener("mouseup", endHandler);
      } else {
        document.addEventListener("touchmove", moveHandler, { passive: false });
        document.addEventListener("touchend", endHandler);
      }
      i[scrollbarRail].classList.add(cls.state.clicking);
    }
    e.stopPropagation();
    if (e.cancelable) {
      e.preventDefault();
    }
  }
  i[scrollbarAxis].addEventListener("mousedown", bindMoves);
  i[scrollbarAxis].addEventListener("touchstart", bindMoves);
}
function keyboard(i) {
  var element = i.element;
  var elementHovered = function() {
    return matches(element, ":hover");
  };
  var scrollbarFocused = function() {
    return matches(i.scrollbarX, ":focus") || matches(i.scrollbarY, ":focus");
  };
  function shouldPreventDefault(deltaX, deltaY) {
    var scrollTop = Math.floor(element.scrollTop);
    if (deltaX === 0) {
      if (!i.scrollbarYActive) {
        return false;
      }
      if (scrollTop === 0 && deltaY > 0 || scrollTop >= i.contentHeight - i.containerHeight && deltaY < 0) {
        return !i.settings.wheelPropagation;
      }
    }
    var scrollLeft = element.scrollLeft;
    if (deltaY === 0) {
      if (!i.scrollbarXActive) {
        return false;
      }
      if (scrollLeft === 0 && deltaX < 0 || scrollLeft >= i.contentWidth - i.containerWidth && deltaX > 0) {
        return !i.settings.wheelPropagation;
      }
    }
    return true;
  }
  i.event.bind(i.ownerDocument, "keydown", function(e) {
    if (e.isDefaultPrevented && e.isDefaultPrevented() || e.defaultPrevented) {
      return;
    }
    if (!elementHovered() && !scrollbarFocused()) {
      return;
    }
    var activeElement = document.activeElement ? document.activeElement : i.ownerDocument.activeElement;
    if (activeElement) {
      if (activeElement.tagName === "IFRAME") {
        activeElement = activeElement.contentDocument.activeElement;
      } else {
        while (activeElement.shadowRoot) {
          activeElement = activeElement.shadowRoot.activeElement;
        }
      }
      if (isEditable(activeElement)) {
        return;
      }
    }
    var deltaX = 0;
    var deltaY = 0;
    switch (e.which) {
      case 37:
        if (e.metaKey) {
          deltaX = -i.contentWidth;
        } else if (e.altKey) {
          deltaX = -i.containerWidth;
        } else {
          deltaX = -30;
        }
        break;
      case 38:
        if (e.metaKey) {
          deltaY = i.contentHeight;
        } else if (e.altKey) {
          deltaY = i.containerHeight;
        } else {
          deltaY = 30;
        }
        break;
      case 39:
        if (e.metaKey) {
          deltaX = i.contentWidth;
        } else if (e.altKey) {
          deltaX = i.containerWidth;
        } else {
          deltaX = 30;
        }
        break;
      case 40:
        if (e.metaKey) {
          deltaY = -i.contentHeight;
        } else if (e.altKey) {
          deltaY = -i.containerHeight;
        } else {
          deltaY = -30;
        }
        break;
      case 32:
        if (e.shiftKey) {
          deltaY = i.containerHeight;
        } else {
          deltaY = -i.containerHeight;
        }
        break;
      case 33:
        deltaY = i.containerHeight;
        break;
      case 34:
        deltaY = -i.containerHeight;
        break;
      case 36:
        deltaY = i.contentHeight;
        break;
      case 35:
        deltaY = -i.contentHeight;
        break;
      default:
        return;
    }
    if (i.settings.suppressScrollX && deltaX !== 0) {
      return;
    }
    if (i.settings.suppressScrollY && deltaY !== 0) {
      return;
    }
    element.scrollTop -= deltaY;
    element.scrollLeft += deltaX;
    updateGeometry(i);
    if (shouldPreventDefault(deltaX, deltaY)) {
      e.preventDefault();
    }
  });
}
function wheel(i) {
  var element = i.element;
  function shouldPreventDefault(deltaX, deltaY) {
    var roundedScrollTop = Math.floor(element.scrollTop);
    var isTop = element.scrollTop === 0;
    var isBottom = roundedScrollTop + element.offsetHeight === element.scrollHeight;
    var isLeft = element.scrollLeft === 0;
    var isRight = element.scrollLeft + element.offsetWidth === element.scrollWidth;
    var hitsBound;
    if (Math.abs(deltaY) > Math.abs(deltaX)) {
      hitsBound = isTop || isBottom;
    } else {
      hitsBound = isLeft || isRight;
    }
    return hitsBound ? !i.settings.wheelPropagation : true;
  }
  function getDeltaFromEvent(e) {
    var deltaX = e.deltaX;
    var deltaY = -1 * e.deltaY;
    if (typeof deltaX === "undefined" || typeof deltaY === "undefined") {
      deltaX = -1 * e.wheelDeltaX / 6;
      deltaY = e.wheelDeltaY / 6;
    }
    if (e.deltaMode && e.deltaMode === 1) {
      deltaX *= 10;
      deltaY *= 10;
    }
    if (deltaX !== deltaX && deltaY !== deltaY) {
      deltaX = 0;
      deltaY = e.wheelDelta;
    }
    if (e.shiftKey) {
      return [-deltaY, -deltaX];
    }
    return [deltaX, deltaY];
  }
  function shouldBeConsumedByChild(target, deltaX, deltaY) {
    if (!env.isWebKit && element.querySelector("select:focus")) {
      return true;
    }
    if (!element.contains(target)) {
      return false;
    }
    var cursor = target;
    while (cursor && cursor !== element) {
      if (cursor.classList.contains(cls.element.consuming)) {
        return true;
      }
      var style = get(cursor);
      if (deltaY && style.overflowY.match(/(scroll|auto)/)) {
        var maxScrollTop = cursor.scrollHeight - cursor.clientHeight;
        if (maxScrollTop > 0) {
          if (cursor.scrollTop > 0 && deltaY < 0 || cursor.scrollTop < maxScrollTop && deltaY > 0) {
            return true;
          }
        }
      }
      if (deltaX && style.overflowX.match(/(scroll|auto)/)) {
        var maxScrollLeft = cursor.scrollWidth - cursor.clientWidth;
        if (maxScrollLeft > 0) {
          if (cursor.scrollLeft > 0 && deltaX < 0 || cursor.scrollLeft < maxScrollLeft && deltaX > 0) {
            return true;
          }
        }
      }
      cursor = cursor.parentNode;
    }
    return false;
  }
  function mousewheelHandler(e) {
    var ref = getDeltaFromEvent(e);
    var deltaX = ref[0];
    var deltaY = ref[1];
    if (shouldBeConsumedByChild(e.target, deltaX, deltaY)) {
      return;
    }
    var shouldPrevent = false;
    if (!i.settings.useBothWheelAxes) {
      element.scrollTop -= deltaY * i.settings.wheelSpeed;
      element.scrollLeft += deltaX * i.settings.wheelSpeed;
    } else if (i.scrollbarYActive && !i.scrollbarXActive) {
      if (deltaY) {
        element.scrollTop -= deltaY * i.settings.wheelSpeed;
      } else {
        element.scrollTop += deltaX * i.settings.wheelSpeed;
      }
      shouldPrevent = true;
    } else if (i.scrollbarXActive && !i.scrollbarYActive) {
      if (deltaX) {
        element.scrollLeft += deltaX * i.settings.wheelSpeed;
      } else {
        element.scrollLeft -= deltaY * i.settings.wheelSpeed;
      }
      shouldPrevent = true;
    }
    updateGeometry(i);
    shouldPrevent = shouldPrevent || shouldPreventDefault(deltaX, deltaY);
    if (shouldPrevent && !e.ctrlKey) {
      e.stopPropagation();
      e.preventDefault();
    }
  }
  if (typeof window.onwheel !== "undefined") {
    i.event.bind(element, "wheel", mousewheelHandler);
  } else if (typeof window.onmousewheel !== "undefined") {
    i.event.bind(element, "mousewheel", mousewheelHandler);
  }
}
function touch(i) {
  if (!env.supportsTouch && !env.supportsIePointer) {
    return;
  }
  var element = i.element;
  var state = {
    startOffset: {},
    startTime: 0,
    speed: {},
    easingLoop: null
  };
  function shouldPrevent(deltaX, deltaY) {
    var scrollTop = Math.floor(element.scrollTop);
    var scrollLeft = element.scrollLeft;
    var magnitudeX = Math.abs(deltaX);
    var magnitudeY = Math.abs(deltaY);
    if (magnitudeY > magnitudeX) {
      if (deltaY < 0 && scrollTop === i.contentHeight - i.containerHeight || deltaY > 0 && scrollTop === 0) {
        return window.scrollY === 0 && deltaY > 0 && env.isChrome;
      }
    } else if (magnitudeX > magnitudeY) {
      if (deltaX < 0 && scrollLeft === i.contentWidth - i.containerWidth || deltaX > 0 && scrollLeft === 0) {
        return true;
      }
    }
    return true;
  }
  function applyTouchMove(differenceX, differenceY) {
    element.scrollTop -= differenceY;
    element.scrollLeft -= differenceX;
    updateGeometry(i);
  }
  function getTouch(e) {
    if (e.targetTouches) {
      return e.targetTouches[0];
    }
    return e;
  }
  function shouldHandle(e) {
    if (e.target === i.scrollbarX || e.target === i.scrollbarY) {
      return false;
    }
    if (e.pointerType && e.pointerType === "pen" && e.buttons === 0) {
      return false;
    }
    if (e.targetTouches && e.targetTouches.length === 1) {
      return true;
    }
    if (e.pointerType && e.pointerType !== "mouse" && e.pointerType !== e.MSPOINTER_TYPE_MOUSE) {
      return true;
    }
    return false;
  }
  function touchStart(e) {
    if (!shouldHandle(e)) {
      return;
    }
    var touch2 = getTouch(e);
    state.startOffset.pageX = touch2.pageX;
    state.startOffset.pageY = touch2.pageY;
    state.startTime = (/* @__PURE__ */ new Date()).getTime();
    if (state.easingLoop !== null) {
      clearInterval(state.easingLoop);
    }
  }
  function shouldBeConsumedByChild(target, deltaX, deltaY) {
    if (!element.contains(target)) {
      return false;
    }
    var cursor = target;
    while (cursor && cursor !== element) {
      if (cursor.classList.contains(cls.element.consuming)) {
        return true;
      }
      var style = get(cursor);
      if (deltaY && style.overflowY.match(/(scroll|auto)/)) {
        var maxScrollTop = cursor.scrollHeight - cursor.clientHeight;
        if (maxScrollTop > 0) {
          if (cursor.scrollTop > 0 && deltaY < 0 || cursor.scrollTop < maxScrollTop && deltaY > 0) {
            return true;
          }
        }
      }
      if (deltaX && style.overflowX.match(/(scroll|auto)/)) {
        var maxScrollLeft = cursor.scrollWidth - cursor.clientWidth;
        if (maxScrollLeft > 0) {
          if (cursor.scrollLeft > 0 && deltaX < 0 || cursor.scrollLeft < maxScrollLeft && deltaX > 0) {
            return true;
          }
        }
      }
      cursor = cursor.parentNode;
    }
    return false;
  }
  function touchMove(e) {
    if (shouldHandle(e)) {
      var touch2 = getTouch(e);
      var currentOffset = { pageX: touch2.pageX, pageY: touch2.pageY };
      var differenceX = currentOffset.pageX - state.startOffset.pageX;
      var differenceY = currentOffset.pageY - state.startOffset.pageY;
      if (shouldBeConsumedByChild(e.target, differenceX, differenceY)) {
        return;
      }
      applyTouchMove(differenceX, differenceY);
      state.startOffset = currentOffset;
      var currentTime = (/* @__PURE__ */ new Date()).getTime();
      var timeGap = currentTime - state.startTime;
      if (timeGap > 0) {
        state.speed.x = differenceX / timeGap;
        state.speed.y = differenceY / timeGap;
        state.startTime = currentTime;
      }
      if (shouldPrevent(differenceX, differenceY)) {
        if (e.cancelable) {
          e.preventDefault();
        }
      }
    }
  }
  function touchEnd() {
    if (i.settings.swipeEasing) {
      clearInterval(state.easingLoop);
      state.easingLoop = setInterval(function() {
        if (i.isInitialized) {
          clearInterval(state.easingLoop);
          return;
        }
        if (!state.speed.x && !state.speed.y) {
          clearInterval(state.easingLoop);
          return;
        }
        if (Math.abs(state.speed.x) < 0.01 && Math.abs(state.speed.y) < 0.01) {
          clearInterval(state.easingLoop);
          return;
        }
        applyTouchMove(state.speed.x * 30, state.speed.y * 30);
        state.speed.x *= 0.8;
        state.speed.y *= 0.8;
      }, 10);
    }
  }
  if (env.supportsTouch) {
    i.event.bind(element, "touchstart", touchStart);
    i.event.bind(element, "touchmove", touchMove);
    i.event.bind(element, "touchend", touchEnd);
  } else if (env.supportsIePointer) {
    if (window.PointerEvent) {
      i.event.bind(element, "pointerdown", touchStart);
      i.event.bind(element, "pointermove", touchMove);
      i.event.bind(element, "pointerup", touchEnd);
    } else if (window.MSPointerEvent) {
      i.event.bind(element, "MSPointerDown", touchStart);
      i.event.bind(element, "MSPointerMove", touchMove);
      i.event.bind(element, "MSPointerUp", touchEnd);
    }
  }
}
var elMatches, cls, scrollingClassTimeout, EventElement, prototypeAccessors, EventManager, env, activeSlider, defaultSettings, handlers, PerfectScrollbar, perfect_scrollbar_esm_default;
var init_perfect_scrollbar_esm = __esm({
  "node_modules/perfect-scrollbar/dist/perfect-scrollbar.esm.js"() {
    elMatches = typeof Element !== "undefined" && (Element.prototype.matches || Element.prototype.webkitMatchesSelector || Element.prototype.mozMatchesSelector || Element.prototype.msMatchesSelector);
    cls = {
      main: "ps",
      rtl: "ps__rtl",
      element: {
        thumb: function(x) {
          return "ps__thumb-" + x;
        },
        rail: function(x) {
          return "ps__rail-" + x;
        },
        consuming: "ps__child--consume"
      },
      state: {
        focus: "ps--focus",
        clicking: "ps--clicking",
        active: function(x) {
          return "ps--active-" + x;
        },
        scrolling: function(x) {
          return "ps--scrolling-" + x;
        }
      }
    };
    scrollingClassTimeout = { x: null, y: null };
    EventElement = function EventElement2(element) {
      this.element = element;
      this.handlers = {};
    };
    prototypeAccessors = { isEmpty: { configurable: true } };
    EventElement.prototype.bind = function bind(eventName, handler) {
      if (typeof this.handlers[eventName] === "undefined") {
        this.handlers[eventName] = [];
      }
      this.handlers[eventName].push(handler);
      this.element.addEventListener(eventName, handler, false);
    };
    EventElement.prototype.unbind = function unbind(eventName, target) {
      var this$1 = this;
      this.handlers[eventName] = this.handlers[eventName].filter(function(handler) {
        if (target && handler !== target) {
          return true;
        }
        this$1.element.removeEventListener(eventName, handler, false);
        return false;
      });
    };
    EventElement.prototype.unbindAll = function unbindAll() {
      for (var name in this.handlers) {
        this.unbind(name);
      }
    };
    prototypeAccessors.isEmpty.get = function() {
      var this$1 = this;
      return Object.keys(this.handlers).every(
        function(key) {
          return this$1.handlers[key].length === 0;
        }
      );
    };
    Object.defineProperties(EventElement.prototype, prototypeAccessors);
    EventManager = function EventManager2() {
      this.eventElements = [];
    };
    EventManager.prototype.eventElement = function eventElement(element) {
      var ee = this.eventElements.filter(function(ee2) {
        return ee2.element === element;
      })[0];
      if (!ee) {
        ee = new EventElement(element);
        this.eventElements.push(ee);
      }
      return ee;
    };
    EventManager.prototype.bind = function bind2(element, eventName, handler) {
      this.eventElement(element).bind(eventName, handler);
    };
    EventManager.prototype.unbind = function unbind2(element, eventName, handler) {
      var ee = this.eventElement(element);
      ee.unbind(eventName, handler);
      if (ee.isEmpty) {
        this.eventElements.splice(this.eventElements.indexOf(ee), 1);
      }
    };
    EventManager.prototype.unbindAll = function unbindAll2() {
      this.eventElements.forEach(function(e) {
        return e.unbindAll();
      });
      this.eventElements = [];
    };
    EventManager.prototype.once = function once(element, eventName, handler) {
      var ee = this.eventElement(element);
      var onceHandler = function(evt) {
        ee.unbind(eventName, onceHandler);
        handler(evt);
      };
      ee.bind(eventName, onceHandler);
    };
    env = {
      isWebKit: typeof document !== "undefined" && "WebkitAppearance" in document.documentElement.style,
      supportsTouch: typeof window !== "undefined" && ("ontouchstart" in window || "maxTouchPoints" in window.navigator && window.navigator.maxTouchPoints > 0 || window.DocumentTouch && document instanceof window.DocumentTouch),
      supportsIePointer: typeof navigator !== "undefined" && navigator.msMaxTouchPoints,
      isChrome: typeof navigator !== "undefined" && /Chrome/i.test(navigator && navigator.userAgent)
    };
    activeSlider = null;
    defaultSettings = function() {
      return {
        handlers: ["click-rail", "drag-thumb", "keyboard", "wheel", "touch"],
        maxScrollbarLength: null,
        minScrollbarLength: null,
        scrollingThreshold: 1e3,
        scrollXMarginOffset: 0,
        scrollYMarginOffset: 0,
        suppressScrollX: false,
        suppressScrollY: false,
        swipeEasing: true,
        useBothWheelAxes: false,
        wheelPropagation: true,
        wheelSpeed: 1
      };
    };
    handlers = {
      "click-rail": clickRail,
      "drag-thumb": setupScrollHandlers,
      keyboard,
      wheel,
      touch
    };
    PerfectScrollbar = function PerfectScrollbar2(element, userSettings) {
      var this$1 = this;
      if (userSettings === void 0) userSettings = {};
      if (typeof element === "string") {
        element = document.querySelector(element);
      }
      if (!element || !element.nodeName) {
        throw new Error("no element is specified to initialize PerfectScrollbar");
      }
      this.element = element;
      element.classList.add(cls.main);
      this.settings = defaultSettings();
      for (var key in userSettings) {
        this.settings[key] = userSettings[key];
      }
      this.containerWidth = null;
      this.containerHeight = null;
      this.contentWidth = null;
      this.contentHeight = null;
      var focus = function() {
        return element.classList.add(cls.state.focus);
      };
      var blur = function() {
        return element.classList.remove(cls.state.focus);
      };
      this.isRtl = get(element).direction === "rtl";
      if (this.isRtl === true) {
        element.classList.add(cls.rtl);
      }
      this.isNegativeScroll = function() {
        var originalScrollLeft = element.scrollLeft;
        var result = null;
        element.scrollLeft = -1;
        result = element.scrollLeft < 0;
        element.scrollLeft = originalScrollLeft;
        return result;
      }();
      this.negativeScrollAdjustment = this.isNegativeScroll ? element.scrollWidth - element.clientWidth : 0;
      this.event = new EventManager();
      this.ownerDocument = element.ownerDocument || document;
      this.scrollbarXRail = div(cls.element.rail("x"));
      element.appendChild(this.scrollbarXRail);
      this.scrollbarX = div(cls.element.thumb("x"));
      this.scrollbarXRail.appendChild(this.scrollbarX);
      this.scrollbarX.setAttribute("tabindex", 0);
      this.event.bind(this.scrollbarX, "focus", focus);
      this.event.bind(this.scrollbarX, "blur", blur);
      this.scrollbarXActive = null;
      this.scrollbarXWidth = null;
      this.scrollbarXLeft = null;
      var railXStyle = get(this.scrollbarXRail);
      this.scrollbarXBottom = parseInt(railXStyle.bottom, 10);
      if (isNaN(this.scrollbarXBottom)) {
        this.isScrollbarXUsingBottom = false;
        this.scrollbarXTop = toInt(railXStyle.top);
      } else {
        this.isScrollbarXUsingBottom = true;
      }
      this.railBorderXWidth = toInt(railXStyle.borderLeftWidth) + toInt(railXStyle.borderRightWidth);
      set(this.scrollbarXRail, { display: "block" });
      this.railXMarginWidth = toInt(railXStyle.marginLeft) + toInt(railXStyle.marginRight);
      set(this.scrollbarXRail, { display: "" });
      this.railXWidth = null;
      this.railXRatio = null;
      this.scrollbarYRail = div(cls.element.rail("y"));
      element.appendChild(this.scrollbarYRail);
      this.scrollbarY = div(cls.element.thumb("y"));
      this.scrollbarYRail.appendChild(this.scrollbarY);
      this.scrollbarY.setAttribute("tabindex", 0);
      this.event.bind(this.scrollbarY, "focus", focus);
      this.event.bind(this.scrollbarY, "blur", blur);
      this.scrollbarYActive = null;
      this.scrollbarYHeight = null;
      this.scrollbarYTop = null;
      var railYStyle = get(this.scrollbarYRail);
      this.scrollbarYRight = parseInt(railYStyle.right, 10);
      if (isNaN(this.scrollbarYRight)) {
        this.isScrollbarYUsingRight = false;
        this.scrollbarYLeft = toInt(railYStyle.left);
      } else {
        this.isScrollbarYUsingRight = true;
      }
      this.scrollbarYOuterWidth = this.isRtl ? outerWidth(this.scrollbarY) : null;
      this.railBorderYWidth = toInt(railYStyle.borderTopWidth) + toInt(railYStyle.borderBottomWidth);
      set(this.scrollbarYRail, { display: "block" });
      this.railYMarginHeight = toInt(railYStyle.marginTop) + toInt(railYStyle.marginBottom);
      set(this.scrollbarYRail, { display: "" });
      this.railYHeight = null;
      this.railYRatio = null;
      this.reach = {
        x: element.scrollLeft <= 0 ? "start" : element.scrollLeft >= this.contentWidth - this.containerWidth ? "end" : null,
        y: element.scrollTop <= 0 ? "start" : element.scrollTop >= this.contentHeight - this.containerHeight ? "end" : null
      };
      this.isAlive = true;
      this.settings.handlers.forEach(function(handlerName) {
        return handlers[handlerName](this$1);
      });
      this.lastScrollTop = Math.floor(element.scrollTop);
      this.lastScrollLeft = element.scrollLeft;
      this.event.bind(this.element, "scroll", function(e) {
        return this$1.onScroll(e);
      });
      updateGeometry(this);
    };
    PerfectScrollbar.prototype.update = function update() {
      if (!this.isAlive) {
        return;
      }
      this.negativeScrollAdjustment = this.isNegativeScroll ? this.element.scrollWidth - this.element.clientWidth : 0;
      set(this.scrollbarXRail, { display: "block" });
      set(this.scrollbarYRail, { display: "block" });
      this.railXMarginWidth = toInt(get(this.scrollbarXRail).marginLeft) + toInt(get(this.scrollbarXRail).marginRight);
      this.railYMarginHeight = toInt(get(this.scrollbarYRail).marginTop) + toInt(get(this.scrollbarYRail).marginBottom);
      set(this.scrollbarXRail, { display: "none" });
      set(this.scrollbarYRail, { display: "none" });
      updateGeometry(this);
      processScrollDiff(this, "top", 0, false, true);
      processScrollDiff(this, "left", 0, false, true);
      set(this.scrollbarXRail, { display: "" });
      set(this.scrollbarYRail, { display: "" });
    };
    PerfectScrollbar.prototype.onScroll = function onScroll(e) {
      if (!this.isAlive) {
        return;
      }
      updateGeometry(this);
      processScrollDiff(this, "top", this.element.scrollTop - this.lastScrollTop);
      processScrollDiff(this, "left", this.element.scrollLeft - this.lastScrollLeft);
      this.lastScrollTop = Math.floor(this.element.scrollTop);
      this.lastScrollLeft = this.element.scrollLeft;
    };
    PerfectScrollbar.prototype.destroy = function destroy() {
      if (!this.isAlive) {
        return;
      }
      this.event.unbindAll();
      remove(this.scrollbarX);
      remove(this.scrollbarY);
      remove(this.scrollbarXRail);
      remove(this.scrollbarYRail);
      this.removePsClasses();
      this.element = null;
      this.scrollbarX = null;
      this.scrollbarY = null;
      this.scrollbarXRail = null;
      this.scrollbarYRail = null;
      this.isAlive = false;
    };
    PerfectScrollbar.prototype.removePsClasses = function removePsClasses() {
      this.element.className = this.element.className.split(" ").filter(function(name) {
        return !name.match(/^ps([-_].+|)$/);
      }).join(" ");
    };
    perfect_scrollbar_esm_default = PerfectScrollbar;
  }
});

// node_modules/react-perfect-scrollbar/lib/scrollbar.js
var require_scrollbar = __commonJS({
  "node_modules/react-perfect-scrollbar/lib/scrollbar.js"(exports, module) {
    "use strict";
    Object.defineProperty(exports, "__esModule", {
      value: true
    });
    var _extends = Object.assign || function(target) {
      for (var i = 1; i < arguments.length; i++) {
        var source = arguments[i];
        for (var key in source) {
          if (Object.prototype.hasOwnProperty.call(source, key)) {
            target[key] = source[key];
          }
        }
      }
      return target;
    };
    var _createClass = /* @__PURE__ */ function() {
      function defineProperties(target, props) {
        for (var i = 0; i < props.length; i++) {
          var descriptor = props[i];
          descriptor.enumerable = descriptor.enumerable || false;
          descriptor.configurable = true;
          if ("value" in descriptor) descriptor.writable = true;
          Object.defineProperty(target, descriptor.key, descriptor);
        }
      }
      return function(Constructor, protoProps, staticProps) {
        if (protoProps) defineProperties(Constructor.prototype, protoProps);
        if (staticProps) defineProperties(Constructor, staticProps);
        return Constructor;
      };
    }();
    var _react = require_react();
    var _react2 = _interopRequireDefault(_react);
    var _propTypes = require_prop_types();
    var _perfectScrollbar = (init_perfect_scrollbar_esm(), __toCommonJS(perfect_scrollbar_esm_exports));
    var _perfectScrollbar2 = _interopRequireDefault(_perfectScrollbar);
    function _interopRequireDefault(obj) {
      return obj && obj.__esModule ? obj : { default: obj };
    }
    function _objectWithoutProperties(obj, keys) {
      var target = {};
      for (var i in obj) {
        if (keys.indexOf(i) >= 0) continue;
        if (!Object.prototype.hasOwnProperty.call(obj, i)) continue;
        target[i] = obj[i];
      }
      return target;
    }
    function _classCallCheck(instance, Constructor) {
      if (!(instance instanceof Constructor)) {
        throw new TypeError("Cannot call a class as a function");
      }
    }
    function _possibleConstructorReturn(self, call) {
      if (!self) {
        throw new ReferenceError("this hasn't been initialised - super() hasn't been called");
      }
      return call && (typeof call === "object" || typeof call === "function") ? call : self;
    }
    function _inherits(subClass, superClass) {
      if (typeof superClass !== "function" && superClass !== null) {
        throw new TypeError("Super expression must either be null or a function, not " + typeof superClass);
      }
      subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } });
      if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass;
    }
    var handlerNameByEvent = {
      "ps-scroll-y": "onScrollY",
      "ps-scroll-x": "onScrollX",
      "ps-scroll-up": "onScrollUp",
      "ps-scroll-down": "onScrollDown",
      "ps-scroll-left": "onScrollLeft",
      "ps-scroll-right": "onScrollRight",
      "ps-y-reach-start": "onYReachStart",
      "ps-y-reach-end": "onYReachEnd",
      "ps-x-reach-start": "onXReachStart",
      "ps-x-reach-end": "onXReachEnd"
    };
    Object.freeze(handlerNameByEvent);
    var ScrollBar = function(_Component) {
      _inherits(ScrollBar2, _Component);
      function ScrollBar2(props) {
        _classCallCheck(this, ScrollBar2);
        var _this = _possibleConstructorReturn(this, (ScrollBar2.__proto__ || Object.getPrototypeOf(ScrollBar2)).call(this, props));
        _this.handleRef = _this.handleRef.bind(_this);
        _this._handlerByEvent = {};
        return _this;
      }
      _createClass(ScrollBar2, [{
        key: "componentDidMount",
        value: function componentDidMount() {
          if (this.props.option) {
            console.warn('react-perfect-scrollbar: the "option" prop has been deprecated in favor of "options"');
          }
          this._ps = new _perfectScrollbar2.default(this._container, this.props.options || this.props.option);
          this._updateEventHook();
          this._updateClassName();
        }
      }, {
        key: "componentDidUpdate",
        value: function componentDidUpdate(prevProps) {
          this._updateEventHook(prevProps);
          this.updateScroll();
          if (prevProps.className !== this.props.className) {
            this._updateClassName();
          }
        }
      }, {
        key: "componentWillUnmount",
        value: function componentWillUnmount() {
          var _this2 = this;
          Object.keys(this._handlerByEvent).forEach(function(key) {
            var value = _this2._handlerByEvent[key];
            if (value) {
              _this2._container.removeEventListener(key, value, false);
            }
          });
          this._handlerByEvent = {};
          this._ps.destroy();
          this._ps = null;
        }
      }, {
        key: "_updateEventHook",
        value: function _updateEventHook() {
          var _this3 = this;
          var prevProps = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : {};
          Object.keys(handlerNameByEvent).forEach(function(key) {
            var callback = _this3.props[handlerNameByEvent[key]];
            var prevCallback = prevProps[handlerNameByEvent[key]];
            if (callback !== prevCallback) {
              if (prevCallback) {
                var prevHandler = _this3._handlerByEvent[key];
                _this3._container.removeEventListener(key, prevHandler, false);
                _this3._handlerByEvent[key] = null;
              }
              if (callback) {
                var handler = function handler2() {
                  return callback(_this3._container);
                };
                _this3._container.addEventListener(key, handler, false);
                _this3._handlerByEvent[key] = handler;
              }
            }
          });
        }
      }, {
        key: "_updateClassName",
        value: function _updateClassName() {
          var className = this.props.className;
          var psClassNames = this._container.className.split(" ").filter(function(name) {
            return name.match(/^ps([-_].+|)$/);
          }).join(" ");
          if (this._container) {
            this._container.className = "scrollbar-container" + (className ? " " + className : "") + (psClassNames ? " " + psClassNames : "");
          }
        }
      }, {
        key: "updateScroll",
        value: function updateScroll() {
          this.props.onSync(this._ps);
        }
      }, {
        key: "handleRef",
        value: function handleRef(ref) {
          this._container = ref;
          this.props.containerRef(ref);
        }
      }, {
        key: "render",
        value: function render() {
          var _props = this.props, className = _props.className, style = _props.style, option = _props.option, options = _props.options, containerRef = _props.containerRef, onScrollY = _props.onScrollY, onScrollX = _props.onScrollX, onScrollUp = _props.onScrollUp, onScrollDown = _props.onScrollDown, onScrollLeft = _props.onScrollLeft, onScrollRight = _props.onScrollRight, onYReachStart = _props.onYReachStart, onYReachEnd = _props.onYReachEnd, onXReachStart = _props.onXReachStart, onXReachEnd = _props.onXReachEnd, component = _props.component, onSync = _props.onSync, children = _props.children, remainProps = _objectWithoutProperties(_props, ["className", "style", "option", "options", "containerRef", "onScrollY", "onScrollX", "onScrollUp", "onScrollDown", "onScrollLeft", "onScrollRight", "onYReachStart", "onYReachEnd", "onXReachStart", "onXReachEnd", "component", "onSync", "children"]);
          var Comp = component;
          return _react2.default.createElement(
            Comp,
            _extends({ style, ref: this.handleRef }, remainProps),
            children
          );
        }
      }]);
      return ScrollBar2;
    }(_react.Component);
    exports.default = ScrollBar;
    ScrollBar.defaultProps = {
      className: "",
      style: void 0,
      option: void 0,
      options: void 0,
      containerRef: function containerRef() {
      },
      onScrollY: void 0,
      onScrollX: void 0,
      onScrollUp: void 0,
      onScrollDown: void 0,
      onScrollLeft: void 0,
      onScrollRight: void 0,
      onYReachStart: void 0,
      onYReachEnd: void 0,
      onXReachStart: void 0,
      onXReachEnd: void 0,
      onSync: function onSync(ps) {
        return ps.update();
      },
      component: "div"
    };
    ScrollBar.propTypes = {
      children: _propTypes.PropTypes.node.isRequired,
      className: _propTypes.PropTypes.string,
      style: _propTypes.PropTypes.object,
      option: _propTypes.PropTypes.object,
      options: _propTypes.PropTypes.object,
      containerRef: _propTypes.PropTypes.func,
      onScrollY: _propTypes.PropTypes.func,
      onScrollX: _propTypes.PropTypes.func,
      onScrollUp: _propTypes.PropTypes.func,
      onScrollDown: _propTypes.PropTypes.func,
      onScrollLeft: _propTypes.PropTypes.func,
      onScrollRight: _propTypes.PropTypes.func,
      onYReachStart: _propTypes.PropTypes.func,
      onYReachEnd: _propTypes.PropTypes.func,
      onXReachStart: _propTypes.PropTypes.func,
      onXReachEnd: _propTypes.PropTypes.func,
      onSync: _propTypes.PropTypes.func,
      component: _propTypes.PropTypes.string
    };
    module.exports = exports["default"];
  }
});

// node_modules/react-perfect-scrollbar/lib/index.js
var require_lib = __commonJS({
  "node_modules/react-perfect-scrollbar/lib/index.js"(exports, module) {
    Object.defineProperty(exports, "__esModule", {
      value: true
    });
    var _scrollbar = require_scrollbar();
    var _scrollbar2 = _interopRequireDefault(_scrollbar);
    function _interopRequireDefault(obj) {
      return obj && obj.__esModule ? obj : { default: obj };
    }
    exports.default = _scrollbar2.default;
    module.exports = exports["default"];
  }
});
export default require_lib();
/*! Bundled license information:

perfect-scrollbar/dist/perfect-scrollbar.esm.js:
  (*!
   * perfect-scrollbar v1.5.6
   * Copyright 2024 Hyunje Jun, MDBootstrap and Contributors
   * Licensed under MIT
   *)
*/
//# sourceMappingURL=react-perfect-scrollbar.js.map
