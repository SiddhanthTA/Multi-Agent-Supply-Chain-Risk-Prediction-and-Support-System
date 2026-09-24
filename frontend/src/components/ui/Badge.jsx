/* eslint-disable react-refresh/only-export-components */
import { cva } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground shadow hover:bg-destructive/80",
        outline: "text-foreground",
        high: "border-transparent bg-destructive/10 text-destructive hover:bg-destructive/20",
        critical: "border-transparent bg-destructive text-destructive-foreground shadow hover:bg-destructive/90",
        medium: "border-transparent bg-amber-500/10 text-amber-600 dark:text-amber-500 hover:bg-amber-500/20",
        low: "border-transparent bg-green-500/10 text-green-600 dark:text-green-500 hover:bg-green-500/20",
        info: "border-transparent bg-blue-500/10 text-blue-600 dark:text-blue-500 hover:bg-blue-500/20",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({ className, variant, ...props }) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
