# calculate Pearson's correlation
corrFunction <- function(df) {
    # Select all columns except 'Outcome'
    x <- df[, !names(df) %in% c("Outcome")]

    # Calculate correlation matrix
    corr <- cor(x, method = "pearson")

    return(corr)
}
