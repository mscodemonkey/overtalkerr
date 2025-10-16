# Accessibility Features

Overtalkerr is designed to be accessible to all users, including those using assistive technologies. We follow WCAG 2.1 AA guidelines to ensure our application is usable by everyone.

## Overview

Our commitment to accessibility reflects our understanding that many users may rely on voice assistants precisely because of visual impairments or motor disabilities. We've built accessibility into every aspect of the application.

## WCAG 2.1 AA Compliance

### Color Contrast

All text meets WCAG 2.1 AA contrast requirements:
- **Normal text** (< 18pt): Minimum 4.5:1 contrast ratio
- **Large text** (≥ 18pt): Minimum 3:1 contrast ratio
- **UI components**: Minimum 3:1 contrast ratio

#### Color Improvements Made:
- Body text: Changed from `#666` (5.74:1) to `#4b5563` (7.51:1) ✅
- Labels: Changed from `#374151` to `#1f2937` (higher contrast) ✅
- Help text: Changed from `#666` to `#4b5563` ✅
- Secondary text: Changed from `#999` to `#6b7280` ✅

### Keyboard Navigation

All interactive elements are fully keyboard accessible:

#### Global Keyboard Shortcuts (Test UI)
- **Enter** - Start search (when in form fields)
- **Y** - Confirm "Yes" (when conversation is active)
- **N** - Say "No" / Show next result (when conversation is active)
- **Escape** - Reset conversation
- **Tab** - Navigate between interactive elements
- **Shift+Tab** - Navigate backwards

#### Focus Indicators
All focusable elements have visible focus indicators:
- Inputs/selects: 2px solid blue outline with 2px offset
- Buttons: 2px solid outline with 2px offset
- Links: Browser default or custom outline

#### Skip to Content
Every page includes a "Skip to main content" link that appears on keyboard focus, allowing users to bypass navigation and go directly to the primary content.

### Screen Reader Support

#### ARIA Labels and Roles
All UI elements have appropriate ARIA labels for screen readers:

**Dashboard:**
- Header: `role="banner"`
- Main content: `role="main"` with `id="main-content"`
- Navigation: `role="navigation"` with `aria-label="Main navigation"`
- Statistics region: `role="region"` with descriptive labels
- Status indicators: `role="status"` with `aria-live="polite"`
- Cards: `role="article"` with unique IDs and labels

**Configuration:**
- Form: `aria-label="Configuration settings form"`
- Required fields: `aria-required="true"`
- Form hints: `aria-describedby` linking to help text
- Toggle switch: `role="switch"` with `aria-checked` state
- Status messages: `role="alert"` with `aria-live="polite"`

**Test UI:**
- Conversation flow: `role="log"` with `aria-live="polite"`
- Button groups: `role="group"` with descriptive labels
- Response options: Clear aria-labels ("Confirm yes, this is the correct result")
- Live speech updates: `aria-live="polite"` and `aria-atomic="true"`

#### Live Regions
Dynamic content updates are announced to screen readers:
- Conversation messages: `aria-live="polite"` on conversation container
- Status changes: `aria-live="polite"` on status indicators
- Form validation: `role="alert"` for errors
- Speech responses: `aria-atomic="true"` to read complete updates

#### Hidden Visual Elements
Decorative elements are hidden from screen readers:
- Decorative emojis: `aria-hidden="true"`
- Logo: Descriptive `aria-label` on SVG
- Loading spinners: Part of text announcement

### Form Accessibility

#### Labels and Descriptions
- All form fields have associated `<label>` elements with `for` attributes
- Complex fields use `aria-describedby` to link to help text
- Required fields marked with `aria-required="true"`

#### Error Handling
- Errors are announced via `role="alert"`
- Error messages are associated with relevant fields
- Error states visible both visually and to screen readers

#### Toggle Switches
Custom toggle switches are fully accessible:
- `role="switch"` for proper semantics
- `aria-checked` state updates dynamically
- Keyboard accessible (Space/Enter to toggle)
- `tabindex="0"` for keyboard focus
- Visual focus indicator

### Semantic HTML

All pages use proper semantic HTML5 elements:
- `<header>` for page headers
- `<main>` for primary content
- `<nav>` for navigation
- `<footer>` for footer content
- `<article>` for independent content blocks
- `<form>` with proper structure
- Heading hierarchy (h1 → h2 → h3)

### Language and Readability

- HTML `lang` attribute set to "en"
- Clear, concise language in all UI text
- Meaningful link text (not "click here")
- Descriptive button labels
- Alt text for all images (decorative images marked `aria-hidden`)

## Testing Recommendations

### Keyboard-Only Testing
1. Disconnect mouse/trackpad
2. Use Tab to navigate through all interactive elements
3. Use Enter/Space to activate buttons and links
4. Use arrow keys in select dropdowns
5. Verify all functionality is accessible

### Screen Reader Testing
Recommended screen readers:
- **macOS**: VoiceOver (Cmd+F5)
- **Windows**: NVDA (free) or JAWS
- **Linux**: Orca

Test scenarios:
1. Navigate through all pages using only screen reader
2. Fill out and submit the configuration form
3. Use the test UI to simulate a conversation
4. Verify all status updates are announced
5. Confirm button labels are clear and descriptive

### Color Contrast Testing
Tools:
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Colour Contrast Analyser (CCA)](https://www.tpgi.com/color-contrast-checker/)
- Chrome DevTools Accessibility pane

### Browser Testing
Test with multiple browsers:
- Chrome/Edge (Chromium)
- Firefox
- Safari
- Mobile browsers (iOS Safari, Chrome Mobile)

## Future Improvements

Potential enhancements for even better accessibility:

### High Priority
- [ ] Dark mode/High contrast theme support
- [ ] Font size adjustments
- [ ] Reduced motion option (for animations)
- [ ] Voice control integration testing

### Medium Priority
- [ ] Comprehensive automated accessibility testing in CI/CD
- [ ] User-configurable keyboard shortcuts
- [ ] Screen reader announcement customization
- [ ] Form auto-save for users who need breaks

### Nice to Have
- [ ] Multiple language support
- [ ] Text-to-speech for responses (beyond voice assistant)
- [ ] Dyslexia-friendly font option
- [ ] Guided tours for new users

## Accessibility Statement

We are committed to ensuring digital accessibility for people with disabilities. We continually improve the user experience for everyone and apply relevant accessibility standards.

### Conformance Status
Overtalkerr is **partially conformant** with WCAG 2.1 level AA. This means that some parts of the content do not fully conform to the accessibility standard.

### Feedback
We welcome feedback on the accessibility of Overtalkerr. If you encounter accessibility barriers:

1. **GitHub Issues**: [Report accessibility issues](https://github.com/mscodemonkey/overtalkerr/issues)
2. **Tag**: Use the `accessibility` label
3. **Include**:
   - Description of the issue
   - Page/screen where it occurs
   - Assistive technology used (if applicable)
   - Browser and OS version

### Technical Specifications
Overtalkerr relies on the following technologies:
- HTML5
- CSS3
- JavaScript (ES6+)
- ARIA 1.2

### Limitations and Alternatives
While we strive for full accessibility, some limitations exist:
- Complex visualizations (charts/graphs) may need text alternatives
- Third-party authentication may have additional requirements
- Voice assistant platforms (Alexa, Google, Siri) have their own accessibility features

## Resources

### For Developers
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Articles](https://webaim.org/articles/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)

### For Users
- [VoiceOver User Guide (macOS)](https://support.apple.com/guide/voiceover/welcome/mac)
- [NVDA User Guide](https://www.nvaccess.org/files/nvda/documentation/userGuide.html)
- [WebAIM Keyboard Shortcuts](https://webaim.org/articles/keyboard/)

---

**Last Updated**: 2025-10-17
**Version**: 1.0 Beta
**Compliance Level**: WCAG 2.1 AA (Partial)
