import { describe, it, expect } from "vitest";
import {
  ParchmentCard,
  ParchmentCardHeader,
  ParchmentCardTitle,
  ParchmentCardDescription,
  ParchmentCardContent,
  ParchmentCardFooter,
  ParchmentCardSeparator,
  ImperialBadge,
  CalloutBox,
  StatusPill,
  ImperialButton,
} from "./index";

describe("Imperial Heritage Design System Primitives", () => {
  it("exports all required design system components and subcomponents", () => {
    expect(ParchmentCard).toBeDefined();
    expect(ParchmentCardHeader).toBeDefined();
    expect(ParchmentCardTitle).toBeDefined();
    expect(ParchmentCardDescription).toBeDefined();
    expect(ParchmentCardContent).toBeDefined();
    expect(ParchmentCardFooter).toBeDefined();
    expect(ParchmentCardSeparator).toBeDefined();
    expect(ImperialBadge).toBeDefined();
    expect(CalloutBox).toBeDefined();
    expect(StatusPill).toBeDefined();
    expect(ImperialButton).toBeDefined();
  });

  it("ParchmentCard component has proper displayName", () => {
    expect(ParchmentCard.displayName).toBe("ParchmentCard");
  });

  it("ImperialBadge component has proper displayName", () => {
    expect(ImperialBadge.displayName).toBe("ImperialBadge");
  });

  it("StatusPill component has proper displayName", () => {
    expect(StatusPill.displayName).toBe("StatusPill");
  });

  it("ImperialButton component has proper displayName", () => {
    expect(ImperialButton.displayName).toBe("ImperialButton");
  });

  it("CalloutBox is a callable functional component", () => {
    expect(typeof CalloutBox).toBe("function");
  });
});
